"""Trace generated atlases only; never loads or borrows an existing font."""
from pathlib import Path
import json, hashlib, unicodedata, shutil
import cv2
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.ttLib import TTFont, newTable
from vertical import VERSION, ROTATED, SHIFTED
from metadata import apply_metadata, verify_metadata
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'output'; QA=ROOT/'qa'
OUT.mkdir(exist_ok=True); QA.mkdir(exist_ok=True)
shutil.copyfile(ROOT/'LICENSE',OUT/'LICENSE.txt')
m=json.loads((ROOT/'sources/manifest.json').read_text())
shapes={}; report=[]
for batch in m['batches']:
 path=ROOT/f"sources/sheets/sheet-{batch['id']}.png"
 image=np.array(Image.open(path).convert('RGB'))
 gray=cv2.cvtColor(image,cv2.COLOR_RGB2GRAY)
 h,w=gray.shape
 for k,ch in enumerate(batch['chars']):
  row,col=divmod(k,6)
  x0,x1=(round(batch['column_bounds'][row][col]*w),round(batch['column_bounds'][row][col+1]*w)) if 'column_bounds' in batch else (round(col*w/6),round((col+1)*w/6))
  y0,y1=(round(batch['row_bounds'][row]*h),round(batch['row_bounds'][row+1]*h)) if 'row_bounds' in batch else (round(row*h/8),round((row+1)*h/8))
  cell=gray[y0:y1,x0:x1]
  mask=(cell<155).astype(np.uint8)*255
  n,labels,stats,_=cv2.connectedComponentsWithStats(mask,8)
  for j in range(1,n):
   if stats[j,cv2.CC_STAT_AREA]<max(3,mask.size*.00007): mask[labels==j]=0
  ys,xs=np.nonzero(mask)
  if not len(xs): raise ValueError(f'Empty glyph {ch} in {path}')
  contours,hierarchy=cv2.findContours(mask,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
  contours_out=[]
  for j,contour in enumerate(contours):
   if abs(cv2.contourArea(contour))<2: continue
   pts=cv2.approxPolyDP(contour,.38,True)[:,0,:].astype(float)
   if len(pts)<3:continue
   # Map the regular atlas cell into the 1000-unit em; preserve relative sizes.
   pts[:,0]=pts[:,0]/(x1-x0)*1000
   pts[:,1]=880-pts[:,1]/(y1-y0)*1000
   pts=np.rint(pts).astype(int)
   depth=0; parent=hierarchy[0,j,3]
   while parent!=-1:depth+=1;parent=hierarchy[0,parent,3]
   area=sum(pts[i,0]*pts[(i+1)%len(pts),1]-pts[(i+1)%len(pts),0]*pts[i,1] for i in range(len(pts)))
   # TrueType outer contours clockwise, holes counterclockwise.
   if (area>0)==(depth%2==0):pts=pts[::-1]
   contours_out.append(pts.tolist())
  shapes[ch]=contours_out
  report.append({'character':ch,'unicode':f'U+{ord(ch):04X}','sheet':batch['id'],'cell':k,'ink_pixels':int(len(xs)),'edge_ink':bool(xs.min()==0 or ys.min()==0 or xs.max()==mask.shape[1]-1 or ys.max()==mask.shape[0]-1),'contours':len(contours_out)})
# Repair two rare small kana whose generated atlas shapes lost their identity.
# Reuse image-generated base kana outlines, reduced; no external glyph source.
for small,base in [('ゕ','か'),('ゖ','け')]:
 shapes[small]=[[[round(500+(x-500)*.72),round(30+(y-30)*.72)] for x,y in poly] for poly in shapes[base]]
# Position lower punctuation at the baseline, retaining generated silhouettes.
for ch in '、。.,':
 low=min(y for poly in shapes[ch] for x,y in poly)
 shapes[ch]=[[[x,y-low+10] for x,y in poly] for poly in shapes[ch]]
# Japanese comma and full stop sit at the lower left of their full-width cell.
for ch in '、。':
 left=min(x for poly in shapes[ch] for x,y in poly)
 shapes[ch]=[[[x-left+90,y] for x,y in poly] for poly in shapes[ch]]
# Only whitespace is deliberately empty. Compatibility forms reuse image-generated outlines.
for ch in [' ','\u00a0','\u3000']:shapes[ch]=[]
for cp in range(0xff01,0xff5f):
 source=chr(cp-0xfee0)
 if source in shapes:shapes[chr(cp)]=shapes[source]
shapes['\u3099']=shapes['゛'];shapes['\u309a']=shapes['゜']
names={c:f'uni{ord(c):04X}' for c in shapes}
order=['.notdef']+list(names.values())
metrics={}; outlines={}
for c,gn in names.items():
 width=600 if 0x21<=ord(c)<=0x7e or c in [' ','\u00a0'] else 1000
 if c in '\u3099\u309a':width=0
 coords=shapes[c]
 if 0x21<=ord(c)<=0x7e:coords=[[[round(x*.6),y] for x,y in ps] for ps in coords]
 if c in '\u3099\u309a':coords=[[[round(x*.45)-440,round(y*.45)+430] for x,y in ps] for ps in coords]
 outlines[gn]=coords
 metrics[gn]=(width,min((x for ps in coords for x,y in ps),default=0))
outlines['.notdef']=shapes['？'];metrics['.notdef']=(1000,min(x for ps in shapes['？'] for x,y in ps))
vertical_names={}
for ch in ROTATED+SHIFTED:
 gn=names[ch]+'.vert'
 source=outlines[names[ch]]
 if ch in ROTATED:
  # Clockwise rotation about the em-cell centre (500, 400).
  coords=[[[y+100,900-x] for x,y in poly] for poly in source]
 else:
  right=max(x for poly in source for x,y in poly)
  top=max(y for poly in source for x,y in poly)
  coords=[[[x+910-right,y+810-top] for x,y in poly] for poly in source]
 outlines[gn]=coords
 metrics[gn]=(1000,min(x for poly in coords for x,y in poly))
 order.append(gn)
 vertical_names[ch]=gn
(QA/'vertical-glyphs.json').write_text(json.dumps({'rotated_clockwise':ROTATED,'translated_upper_right':SHIFTED,'glyphs':vertical_names},ensure_ascii=False,indent=2))
for is_ttf in [True,False]:
 fb=FontBuilder(1000,isTTF=is_ttf)
 fb.setupGlyphOrder(order)
 fb.setupCharacterMap({ord(c):gn for c,gn in names.items()})
 glyphs={}
 for gn,polys in outlines.items():
  pen=TTGlyphPen(None) if is_ttf else T2CharStringPen(metrics[gn][0],None)
  for points in polys:
   pen.moveTo(tuple(points[0]))
   for pt in points[1:]:pen.lineTo(tuple(pt))
   pen.closePath()
  glyphs[gn]=pen.glyph() if is_ttf else pen.getCharString(optimize=False)
 if is_ttf:fb.setupGlyf(glyphs)
 else:fb.setupCFF('ChochutenKacho-Regular',{'FullName':'Chochuten Kacho Regular','FamilyName':'Chochuten Kacho','Weight':'Regular','Notice':'Dedicated to the public domain under CC0 1.0 Universal.'},glyphs,{})
 fb.setupHorizontalMetrics(metrics)
 fb.setupHorizontalHeader(ascent=900,descent=-140,lineGap=100)
 fb.setupNameTable({'familyName':'Chochuten Kacho','styleName':'Regular','uniqueFontIdentifier':f'ChochutenKacho-Regular-{VERSION}','fullName':'Chochuten Kacho Regular','psName':'ChochutenKacho-Regular','version':f'Version {VERSION}','copyright':'Dedicated to the public domain under CC0 1.0 Universal.','licenseDescription':'CC0 1.0 Universal. To the extent possible under law, all copyright and related or neighboring rights in this font have been waived. See LICENSE.txt.','licenseInfoURL':'https://creativecommons.org/publicdomain/zero/1.0/','description':'Original bird-and-insect seal inspired Japanese display font. Image-generated source atlases.'})
 fb.font['head'].fontRevision=float(VERSION)
 fb.font['name'].setName('鳥虫篆 花鳥',1,3,1,0x411)
 fb.font['name'].setName('標準',2,3,1,0x411)
 fb.font['name'].setName('鳥虫篆 花鳥 標準',4,3,1,0x411)
 # Modern applications may prefer typographic family/subfamily names.
 for language,family,style in [(0x409,'Chochuten Kacho','Regular'),(0x411,'鳥虫篆 花鳥','標準')]:
  fb.font['name'].setName(family,16,3,1,language)
  fb.font['name'].setName(style,17,3,1,language)
 # Declare Japanese (Shift JIS) support for OS language filtering.
 # setupOS2 infers Unicode ranges, but does not infer code-page ranges.
 fb.setupOS2(sTypoAscender=900,sTypoDescender=-140,sTypoLineGap=100,usWinAscent=1050,usWinDescent=200,fsType=0,ulCodePageRange1=(1<<17),ulCodePageRange2=0)
 fb.setupPost(keepGlyphNames=True)
 fb.setupVerticalMetrics({gn:(1000,900-max((y for ps in polys for x,y in ps),default=0)) for gn,polys in outlines.items()})
 fb.setupVerticalHeader(ascent=500,descent=-500)
 if not is_ttf:
  vorg=newTable('VORG')
  vorg.majorVersion=1;vorg.minorVersion=0
  vorg.defaultVertOriginY=900;vorg.VOriginRecords={}
  fb.font['VORG']=vorg
 fb.setupMaxp()
 rules=[]
 for c in shapes:
  decomp=unicodedata.normalize('NFD',c)
  if len(decomp)==2 and decomp[1] in '\u3099\u309a' and all(x in names for x in decomp):
   rules.append(f'sub {names[decomp[0]]} {names[decomp[1]]} by {names[c]};')
 features='languagesystem DFLT dflt; languagesystem hani dflt; languagesystem hani JAN; languagesystem kana dflt; languagesystem kana JAN; languagesystem latn dflt;\n'
 if rules:features+='feature ccmp {\n'+'\n'.join(rules)+'\n} ccmp;\n'
 vertical_rules='\n'.join(f'sub {names[ch]} by {gn};' for ch,gn in vertical_names.items())
 for tag in ['vert','vrt2']:
  features+=f'feature {tag} {{\n{vertical_rules}\n}} {tag};\n'
 addOpenTypeFeaturesFromString(fb.font,features)
 apply_metadata(fb.font)
 fb.font.recalcTimestamp=False;fb.font['head'].created=fb.font['head'].modified=3875126400
 suffix='ttf' if is_ttf else 'otf'
 fb.save(OUT/f'ChochutenKacho-Regular.{suffix}')
font=ImageFont.truetype(str(OUT/'ChochutenKacho-Regular.ttf'),100)
label=ImageFont.load_default(size=16)
for batch in m['batches']:
 im=Image.new('RGB',(1200,1600),'#faf8f2');d=ImageDraw.Draw(im)
 for k,ch in enumerate(batch['chars']):
  row,col=divmod(k,6);x=col*200;y=row*200
  d.text((x+45,y+20),ch,font=font,fill='#172b28')
  d.text((x+20,y+170),f'{k+1:02} U+{ord(ch):04X}',font=label,fill='#666666')
 im.save(QA/f"font-sheet-{batch['id']}.png")
(OUT/'characters.txt').write_text(''.join(shapes)+'\n')
(QA/'glyph-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
checks={}
for suffix in ['ttf','otf']:
 path=OUT/f'ChochutenKacho-Regular.{suffix}';f=TTFont(path)
 cmap=f.getBestCmap()
 verify_metadata(f)
 assert set(map(ord,m['characters']))<=set(cmap)
 assert all(f['hmtx'][cmap[ord(c)]][0]==1000 for c in m['sets']['grade1']+m['sets']['grade2'])
 assert all(f['hmtx'][cmap[ord(c)]][0]==0 for c in '\u3099\u309a')
 assert ('glyf' in f)==(suffix=='ttf')
 assert ('CFF ' in f)==(suffix=='otf')
 assert 'CC0 1.0 Universal' in f['name'].getDebugName(13)
 assert f['name'].getDebugName(14)=='https://creativecommons.org/publicdomain/zero/1.0/'
 assert f['OS/2'].ulCodePageRange1 & (1<<17), 'Japanese code-page support must be declared'
 for name_id,expected in [(1,'鳥虫篆 花鳥'),(2,'標準'),(4,'鳥虫篆 花鳥 標準'),(16,'鳥虫篆 花鳥'),(17,'標準')]:
  assert f['name'].getName(name_id,3,1,0x411).toUnicode()==expected
 checks[suffix]={'version':VERSION,'unicode_mappings':len(cmap),'glyphs':len(f.getGlyphOrder()),'vertical_alternates':len(vertical_names),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'grade1':80,'grade2':160}
(QA/'validation.json').write_text(json.dumps(checks,indent=2))
print(json.dumps(checks,indent=2))
assert not any(r['edge_ink'] for r in report), 'Glyph touches segmentation edge; review qa/glyph-report.json'
import subprocess,sys
subprocess.run([sys.executable,str(ROOT/'scripts/specimen.py')],check=True)
print('All glyphs clear segmentation edges; specimens rendered.')

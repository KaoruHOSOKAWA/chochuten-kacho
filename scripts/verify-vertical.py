"""Exercise actual OpenType substitutions and vertical placement with HarfBuzz."""
from pathlib import Path
import json
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.boundsPen import BoundsPen
from PIL import Image, ImageDraw, ImageFont
from vertical import ROTATED, SHIFTED

R=Path(__file__).resolve().parent.parent
chars=ROTATED+SHIFTED
results={}

def shape(font,text,direction='ttb',features=None,script='Hani'):
    buf=hb.Buffer()
    buf.add_str(text)
    buf.direction=direction
    buf.script=script
    buf.language='ja'
    hb.shape(font,buf,features)
    return list(zip(buf.glyph_infos,buf.glyph_positions))

def bounds(gs,name):
    pen=BoundsPen(gs)
    gs[name].draw(pen)
    return pen.bounds

for ext in ['ttf','otf']:
    path=R/f'output/ChochutenKacho-Regular.{ext}'
    tt=TTFont(path)
    gs=tt.getGlyphSet()
    cmap=tt.getBestCmap()
    font=hb.Font(hb.Face(path.read_bytes()))
    font.scale=(1000,1000)
    hb.ot_font_set_funcs(font)
    tags={record.FeatureTag for record in tt['GSUB'].table.FeatureList.FeatureRecord}
    assert {'vert','vrt2'}<=tags
    count=0
    for ch in chars:
        base=cmap[ord(ch)]; alt=base+'.vert'
        a=bounds(gs,base); b=bounds(gs,alt)
        if ch in ROTATED:
            expected=(a[1]+100,900-a[2],a[3]+100,900-a[0])
        else:
            expected=(910-(a[2]-a[0]),810-(a[3]-a[1]),910,810)
            assert a[0]==90 and a[1]==10
        assert b==expected,(ext,ch,a,b,expected)
        assert 0<=b[0]<b[2]<=1000 and -100<=b[1]<b[3]<=900
        assert tt['vmtx'][alt]==(1000,900-b[3])
        for script in ['Hani','Kana','Zyyy']:
            horizontal=shape(font,ch,'ltr',script=script)
            assert tt.getGlyphName(horizontal[0][0].codepoint)==base
            disabled=shape(font,ch,features={'vert':False,'vrt2':False},script=script)
            assert tt.getGlyphName(disabled[0][0].codepoint)==base
            for features in [None,{'vert':True,'vrt2':False},{'vert':False,'vrt2':True},{'vert':True,'vrt2':True}]:
                shaped=shape(font,ch,features=features,script=script)
                assert len(shaped)==1
                info,pos=shaped[0]
                assert tt.getGlyphName(info.codepoint)==alt,(ext,ch,script,features)
                assert (pos.x_advance,pos.y_advance)==(0,-1000)
                assert (pos.x_offset,pos.y_offset)==(-500,-900)
                count+=1
    for text in ['「花の色、空の青。」','『山川草木。』','（天地日月）','［鳥の声］','｛はるの山｝','〈風と鳥〉','《月の光》','【あいうえお】','コーヒー〜…‥：；']:
        shaped=shape(font,text)
        assert len(shaped)==len(text)
        for ch,(info,pos) in zip(text,shaped):
            assert tt.getGlyphName(info.codepoint)==cmap[ord(ch)]+('.vert' if ch in chars else '')
    results[ext]={'vertical_alternates':len(chars),'rotation':len(ROTATED),'translation':len(SHIFTED),'shaping_checks':count,'features':['vert','vrt2'],'horizontal_forms_preserved':True,'bounds_and_vertical_origins':'passed','context_shaping':'passed'}

# Draw the actual shaped TTF glyphs with their HarfBuzz positions, including holes.
tt=TTFont(R/'output/ChochutenKacho-Regular.ttf')
font=hb.Font(hb.Face((R/'output/ChochutenKacho-Regular.ttf').read_bytes()))
font.scale=(1000,1000);hb.ot_font_set_funcs(font)

def draw_glyph(im,name,origin_x,origin_y,scale):
    glyph=tt['glyf'][name]
    if not glyph.numberOfContours:return
    points,ends,flags=glyph.getCoordinates(tt['glyf'])
    assert all(flag&1 for flag in flags), 'Preview renderer expects the line contours produced by this font builder'
    mask=Image.new('L',im.size,0);d=ImageDraw.Draw(mask)
    start=0
    for end in ends:
        contour=list(points[start:end+1]);start=end+1
        area=sum(x*contour[(k+1)%len(contour)][1]-contour[(k+1)%len(contour)][0]*y for k,(x,y) in enumerate(contour))
        poly=[(round(origin_x+x*scale),round(origin_y-y*scale)) for x,y in contour]
        d.polygon(poly,fill=255 if area<0 else 0)
    im.paste('#173e36',(0,0),mask)

def draw_run(im,text,x,y,size,direction='ttb'):
    px=py=0
    for info,pos in shape(font,text,direction):
        draw_glyph(im,tt.getGlyphName(info.codepoint),x+(px+pos.x_offset)*size/1000,y-(py+pos.y_offset)*size/1000,size/1000)
        px+=pos.x_advance;py+=pos.y_advance

label=ImageFont.load_default(size=18)
im=Image.new('RGB',(1560,1120),'#f7f2e7');d=ImageDraw.Draw(im)
for k,ch in enumerate(chars):
    row,col=divmod(k,6);x=col*260;y=row*280
    d.text((x+12,y+12),f'U+{ord(ch):04X}   H / V',font=label,fill='#6c766d')
    for left in [x+12,x+138]:d.rectangle((left,y+68,left+110,y+178),outline='#c4c9bd')
    draw_run(im,ch,x+12,y+167,110,'ltr')
    draw_run(im,ch,x+193,y+68,110)
im.save(R/'qa/vertical-glyphs.png')

columns=['「花の色、空の青。」','『山川草木。』','（天地日月）','［鳥の声］','｛はるの山｝','〈風と鳥〉','《月の光》','【あいうえお】','コーヒー〜…‥：；']
im=Image.new('RGB',(1800,1550),'#f7f2e7');d=ImageDraw.Draw(im)
d.text((70,35),'CHOCHUTEN KACHO / VERTICAL OPENTYPE / HARFBUZZ',font=label,fill='#6c766d')
for k,text in enumerate(columns):draw_run(im,text,1670-k*190,130,110)
im.save(R/'output/specimen-vertical.png')
(R/'qa/vertical-validation.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(results,ensure_ascii=False,indent=2))

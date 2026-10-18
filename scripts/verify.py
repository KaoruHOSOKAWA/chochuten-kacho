from pathlib import Path
import json
import numpy as np
import cv2
from fontTools.pens.boundsPen import BoundsPen
from PIL import Image,ImageDraw,ImageFont
from fontTools.ttLib import TTFont
R=Path(__file__).resolve().parent.parent
fonts=[TTFont(R/f'output/ChochutenKacho-Regular.{e}') for e in ['ttf','otf']]
cmaps=[f.getBestCmap() for f in fonts];assert cmaps[0]==cmaps[1]
renderers=[ImageFont.truetype(str(R/f'output/ChochutenKacho-Regular.{e}'),192) for e in ['ttf','otf']]
scores=[];tolerant=[];bound_diffs=[]
sets=[f.getGlyphSet() for f in fonts]
for cp in cmaps[0]:
 if chr(cp) in ' \u00a0\u3000':continue
 bounds=[]
 for gs in sets:
  pen=BoundsPen(gs);gs[cmaps[0][cp]].draw(pen);bounds.append(pen.bounds)
 bound_diffs.append(max(abs(a-b) for a,b in zip(*bounds)))
 masks=[]
 for font in renderers:
  im=Image.new('L',(320,320),0);ImageDraw.Draw(im).text((60,240),chr(cp),font=font,fill=255,anchor='ls');masks.append(np.array(im)>127)
 assert all(a.any() for a in masks),f'Empty raster U+{cp:04X}'
 union=(masks[0]|masks[1]).sum();iou=float((masks[0]&masks[1]).sum()/union)
 scores.append((iou,cp))
 near=[cv2.dilate(a.astype('uint8'),np.ones((3,3),'uint8')).astype(bool) for a in masks]
 tolerant.append(min(float((masks[0]&near[1]).sum()/masks[0].sum()),float((masks[1]&near[0]).sum()/masks[1].sum())))
print('Minimum agreement within one pixel:',min(tolerant))
assert min(tolerant)>.98
assert max(bound_diffs)==0
report={'unicode_mappings':len(cmaps[0]),'nonempty_rendered':len(scores),'formats':['TTF quadratic-outline OpenType','OTF CFF-outline OpenType'],'min_ttf_otf_raster_iou':min(s for s,c in scores),'min_one_pixel_tolerant_agreement':min(tolerant),'max_outline_bound_difference_units':max(bound_diffs),'no_segmentation_edge_ink':not any(g['edge_ink'] for g in json.loads((R/'qa/glyph-report.json').read_text())),'docker_execution':'container' if Path('/.dockerenv').exists() else 'local'}
(R/'qa/render-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

"""Measure whitespace between image-generated glyphs; persist reviewable cuts."""
from pathlib import Path
import json
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parent.parent
p=R/'sources/manifest.json';m=json.loads(p.read_text())
for b in m['batches']:
 a=np.array(Image.open(R/f"sources/sheets/sheet-{b['id']}.png").convert('L'))<155
 h,w=a.shape
 y=np.where(a.sum(1)>6)[0];groups=np.split(y,np.where(np.diff(y)>8)[0]+1)
 expected=(len(b['chars'])+5)//6
 assert len(groups)==expected,(b['id'],len(groups),expected)
 ys=[0]+[round((g[-1]+n[0])/2) for g,n in zip(groups,groups[1:])]
 ys+=[h if expected==8 else min(h,int(groups[-1][-1]+(groups[-1][-1]-groups[-1][0])*.3))]
 b['row_bounds']=[v/h for v in ys]
 b['column_bounds']=[]
 for row in range(expected):
  counts=a[ys[row]:ys[row+1]].sum(0);cuts=[0]
  for c in range(1,6):
   target=round(c*w/6);lo=max(cuts[-1]+1,target-40);hi=min(w,target+40)
   blank=np.where(counts[lo:hi]==0)[0]+lo
   runs=np.split(blank,np.where(np.diff(blank)>1)[0]+1)
   runs=[r for r in runs if len(r)>=3]
   if runs:cut=min((round((r[0]+r[-1])/2) for r in runs),key=lambda x:abs(x-target))
   else:cut=target
   cuts.append(cut)
  cuts+=[w];b['column_bounds'].append([x/w for x in cuts])
 print(b['id'],ys)
p.write_text(json.dumps(m,ensure_ascii=False,indent=2))

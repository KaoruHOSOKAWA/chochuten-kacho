import json
from pathlib import Path
G1='一右雨円王音下火花貝学気九休玉金空月犬見五口校左三山子四糸字耳七車手十出女小上森人水正生青夕石赤千川先早草足村大男竹中虫町天田土二日入年白八百文木本名目立力林六'
G2='引羽雲園遠何科夏家歌画回会海絵外角楽活間丸岩顔汽記帰弓牛魚京強教近兄形計元言原戸古午後語工公広交光考行高黄合谷国黒今才細作算止市矢姉思紙寺自時室社弱首秋週春書少場色食心新親図数西声星晴切雪船線前組走多太体台地池知茶昼長鳥朝直通弟店点電刀冬当東答頭同道読内南肉馬売買麦半番父風分聞米歩母方北毎妹万明鳴毛門夜野友用曜来里理話'
assert len(G1)==80 and len(G2)==160
sets={'grade1':G1,'grade2':G2,'hiragana':''.join(chr(i) for i in range(0x3041,0x3097)),'katakana':''.join(chr(i) for i in range(0x30a1,0x30fb)),'ascii':''.join(chr(i) for i in range(33,127)),'punctuation':'、。・「」『』（）［］｛｝〈〉《》【】！？：；ー〜…‥々〆〇゛゜ゝゞヽヾ〒※￥'}
chars=''.join(dict.fromkeys(''.join(sets.values())))
batches=[]
for i in range(0,len(chars),48):
 s=chars[i:i+48]; batches.append({'id':f'{i//48+1:02}','chars':s,'rows':[s[k:k+6] for k in range(0,len(s),6)],'columns':6,'rows_count':8})
extra=''.join(dict.fromkeys(c for c in '篆蟲體印章龍鳳凰夢雅寿福喜美愛永飛舞和吉祥祝禄豊鶴亀桜梅霞虹鷹虎蛇蝶蜂蓮華宝霊神聖祭幸結絆平安楽藝藝雁鳴雫瑞雲紫紅朱翠金銀銅墨筆刻魂' if c not in chars))[:48]
sets['extra']=extra
batches.append({'id':'13','chars':extra,'rows':[extra[k:k+6] for k in range(0,48,6)],'columns':6,'rows_count':8})
chars+=extra
batches[11]['row_bounds']=[0,.21,.37,.535,.705]
Path('sources/manifest.json').write_text(json.dumps({'sets':sets,'characters':chars,'batches':batches},ensure_ascii=False,indent=2))
batches[11]['row_bounds']=[0,.21,.37,.535,.705]
base='''Use case: stylized-concept. Asset type: source glyph atlas for an original Japanese display font, Chochuten Kacho. Create a pure black on pure white glyph sheet, portrait 1536x2048, exactly SIX equal columns and EIGHT equal rows, 48 invisible square cells, no margins outside the grid. One glyph per cell, centered, with 18% clear whitespace padding inside each cell. No visible grid, borders, captions, labels, shadows, colors, paper texture or decoration outside glyphs.\nStyle: elegant ancient Chinese bird-and-insect seal script (鳥虫篆 / 鳥蟲篆), long coiling continuous monoline ink strokes, bird-beak and small bird-eye terminals integrated organically INTO the strokes, graceful insect-like sinuous tails, small teardrop loops. Strong original calligraphic character, consistent stroke thickness around 7% of cell width, smooth clean closed silhouettes for vector tracing. Preserve each requested character's identity and structure. Kana and Latin letters use the SAME serpentine bird-seal aesthetic but remain recognizable. Punctuation should remain functional. No ordinary modern typeface. All strokes solid black, background solid white.\nCRITICAL: follow the exact row-major sequence below, left to right then top to bottom. Each line is one row of six glyphs; spaces are separators, not requested glyphs. Render ONLY these glyphs, no headings or extra marks. Unused cells in the final row and all remaining rows must stay blank.\n'''
for b in batches:
 Path(f"prompts/sheet-{b['id']}.txt").write_text(base+'\n'.join(' '.join(row) for row in b['rows']))
print(len(chars),len(batches))

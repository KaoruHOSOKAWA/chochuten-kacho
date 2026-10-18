from pathlib import Path
import zipfile
from fontTools.ttLib import TTFont
R=Path(__file__).resolve().parent.parent
font=TTFont(R/'output/ChochutenKacho-Regular.ttf')
version=font['name'].getDebugName(5).removeprefix('Version ')
archive=R/f'output/ChochutenKacho-v{version}.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
 for name in ['README.md','LICENSE','Dockerfile','compose.yaml','requirements.txt','.dockerignore','.gitignore']:
  z.write(R/name,'ChochutenKacho/'+name)
 for dirname in ['scripts','sources','prompts','qa','output']:
  for p in sorted((R/dirname).rglob('*')):
   if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.zip':
    z.write(p,'ChochutenKacho/'+str(p.relative_to(R)))
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
print(archive)
print('Release ZIP CRC: passed')

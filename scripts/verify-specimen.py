"""Check the generated catalog against the embedded font and actual shaping."""
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
import base64
import hashlib
import json
import re

from fontTools.ttLib import TTFont
import uharfbuzz as hb

ROOT = Path(__file__).resolve().parent.parent


class Catalog(HTMLParser):
    def __init__(self):
        super().__init__()
        self.cards = []
        self.current = None
        self.ids = []
        self.uses = []
        self.editables = 0
        self.inline_styles = 0

    def handle_starttag(self, tag, attributes):
        attributes = dict(attributes)
        if 'id' in attributes:
            self.ids.append(attributes['id'])
        self.inline_styles += 'style' in attributes
        self.editables += attributes.get('contenteditable') == 'true'
        if tag == 'div' and attributes.get('class') == 'glyph-card':
            self.current = {
                'cp': int(attributes['data-codepoint'][2:], 16),
                'variant': attributes['data-variant'],
            }
            self.cards.append(self.current)
        if tag == 'use':
            self.current['gid'] = int(attributes['href'].removeprefix('#glyph-'))
            self.uses.append(attributes['href'][1:])


page = (ROOT / 'output/specimen.html').read_text()
catalog = Catalog()
catalog.feed(page)
embedded = base64.b64decode(re.search(r'base64,([A-Za-z0-9+/=]+)', page)[1])
assert embedded == (ROOT / 'output/ChochutenKacho-Regular.ttf').read_bytes()
font = TTFont(ROOT / 'output/ChochutenKacho-Regular.ttf')
cmap = font.getBestCmap()
regular = [card for card in catalog.cards if card['variant'] == 'horizontal']
vertical = [card for card in catalog.cards if card['variant'] == 'vertical']
assert Counter(card['cp'] for card in regular) == Counter(cmap.keys())
assert len(vertical) == json.loads((ROOT / 'qa/vertical-validation.json').read_text())['ttf']['vertical_alternates']
assert len(catalog.ids) == len(set(catalog.ids))
assert set(catalog.uses) <= set(catalog.ids)
assert catalog.editables == 1 and catalog.inline_styles == 0
for card in regular:
    assert card['gid'] == font.getGlyphID(cmap[card['cp']])
shaping_font = hb.Font(hb.Face(embedded))
shaping_font.scale = (1000, 1000)
hb.ot_font_set_funcs(shaping_font)
for card in vertical:
    buffer = hb.Buffer()
    buffer.add_str(chr(card['cp']))
    buffer.direction = 'ttb'
    buffer.script = 'Hani'
    buffer.language = 'ja'
    hb.shape(shaping_font, buffer)
    assert len(buffer.glyph_infos) == 1
    assert buffer.glyph_infos[0].codepoint == card['gid']
assert (ROOT / 'README.md').read_text().startswith('![鳥虫篆 花鳥の使用見本](output/specimen.png)')
assert (ROOT / 'output/LICENSE.txt').read_bytes() == (ROOT / 'LICENSE').read_bytes()
report = {
    'font_sha256': hashlib.sha256(embedded).hexdigest(),
    'listed_characters': len(regular),
    'vertical_forms': len(vertical),
    'missing_characters': 0,
    'duplicate_codepoints': 0,
    'unresolved_svg_references': 0,
    'editable_fields': catalog.editables,
    'inline_style_overrides': catalog.inline_styles,
    'vertical_glyphs_match_harfbuzz': True,
    'readme_starts_with_sample_image': True,
    'license': 'CC0-1.0',
}
(ROOT / 'qa/specimen-validation.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))

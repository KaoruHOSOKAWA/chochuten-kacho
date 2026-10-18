"""Build every specimen from the exact font bytes embedded in the HTML."""
from pathlib import Path
from string import Template
import base64
import hashlib
import html
import io
import json
import unicodedata

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = Path(__file__).parent / 'templates'
SAMPLE_SIZE = 84
CATALOG_SIZE = 64
GROUPS = [
    ('grade1', '小学1年の漢字'),
    ('grade2', '小学2年の漢字'),
    ('extra', '追加の漢字'),
    ('hiragana', 'ひらがな'),
    ('katakana', 'カタカナ'),
    ('ascii', '半角英数字・記号'),
    ('punctuation', '約物・記号（横組み）'),
]
CHARACTER_LABELS = {
    0x0020: '半角空白',
    0x00A0: '改行しない空白',
    0x3000: '全角空白',
    0x3099: '結合濁点',
    0x309A: '結合半濁点',
}


def character_groups(cmap, manifest):
    """The cmap controls coverage; the manifest only supplies grouping/order."""
    seen = set()
    groups = []

    def add(key, label, candidates):
        codepoints = list(dict.fromkeys(cp for cp in candidates if cp in cmap and cp not in seen))
        if codepoints:
            seen.update(codepoints)
            groups.append((key, label, codepoints))

    for key, label in GROUPS:
        add(key, label, map(ord, manifest['sets'].get(key, '')))
    add('fullwidth', '全角英数字・記号', range(0xFF01, 0xFF5F))
    add('combining', '結合文字', (cp for cp in sorted(cmap) if unicodedata.combining(chr(cp))))
    add('spaces', '空白', (cp for cp in sorted(cmap) if chr(cp).isspace()))
    add('other', 'その他の収録文字', sorted(cmap))
    assert seen == set(cmap)
    return groups


def vertical_forms(font, cmap):
    """Read actual single-glyph vertical substitutions, deduplicating vert/vrt2."""
    if 'GSUB' not in font:
        return []
    table = font['GSUB'].table
    forms = {}
    for record in table.FeatureList.FeatureRecord:
        if record.FeatureTag not in ('vert', 'vrt2'):
            continue
        for lookup_index in record.Feature.LookupListIndex:
            lookup = table.LookupList.Lookup[lookup_index]
            for subtable in lookup.SubTable:
                if lookup.LookupType == 7:
                    subtable = subtable.ExtSubTable
                if not hasattr(subtable, 'mapping'):
                    raise ValueError('The specimen expects single-glyph vertical substitutions')
                for source, target in subtable.mapping.items():
                    forms.setdefault((source, target), set()).add(record.FeatureTag)
    return [(cp, target, sorted(tags))
            for cp, source in sorted(cmap.items())
            for (base, target), tags in forms.items() if base == source]


def render_catalog(font, cmap, groups, vertical):
    glyph_set = font.getGlyphSet()
    definitions = {}
    upem = font['head'].unitsPerEm
    vertical_origin = font['VORG'].defaultVertOriginY if 'VORG' in font else None

    def glyph_definition(name):
        identifier = f'glyph-{font.getGlyphID(name)}'
        if name not in definitions:
            pen = SVGPathPen(glyph_set)
            glyph_set[name].draw(pen)
            advance = font['hmtx'][name][0]
            origin = vertical_origin
            if origin is None:
                glyph = font['glyf'][name]
                top = glyph.yMax if glyph.numberOfContours else 0
                origin = top + font['vmtx'][name][1]
            x = (upem - advance) / 2
            path = html.escape(pen.getCommands(), quote=True)
            definitions[name] = (
                f'<path id="{identifier}" transform="translate({x:g} {origin:g}) scale(1 -1)" d="{path}"/>'
            )
        return identifier

    def card(cp, name, variant='horizontal', tags=()):
        identifier = glyph_definition(name)
        code = f'U+{cp:04X}'
        label = CHARACTER_LABELS.get(cp, '')
        description = f'{code} {label or unicodedata.name(chr(cp), "名称なし")}'
        if variant == 'vertical':
            description += ' / 縦組み'
        text = html.escape(description, quote=True)
        caption = f'<span class="glyph-code">{code}</span>'
        if label:
            caption += f'<span class="glyph-label">{html.escape(label)}</span>'
        feature = f' data-features="{html.escape(" ".join(tags), quote=True)}"' if tags else ''
        return (
            f'<div class="glyph-card" data-codepoint="{code}" data-variant="{variant}"{feature} title="{text}">'
            f'<svg class="glyph-image" viewBox="0 0 {upem} {upem}" role="img" aria-label="{text}">'
            f'<use href="#{identifier}"/></svg>{caption}</div>'
        )

    sections = []
    for key, label, codepoints in groups:
        cards = ''.join(card(cp, cmap[cp]) for cp in codepoints)
        sections.append(
            f'<section data-section="{key}"><h2>{html.escape(label)} <span class="count">{len(codepoints)}文字</span></h2>'
            f'<div class="glyph-grid">{cards}</div></section>'
        )
    if vertical:
        cards = ''.join(card(cp, name, 'vertical', tags) for cp, name, tags in vertical)
        sections.append(
            f'<section data-section="vertical"><h2>約物・記号（縦組み） <span class="count">{len(vertical)}字形</span></h2>'
            f'<div class="glyph-grid">{cards}</div></section>'
        )
    definitions_svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" class="glyph-definitions" aria-hidden="true">'
        '<defs>' + ''.join(definitions.values()) + '</defs></svg>'
    )
    return definitions_svg, '\n'.join(sections)


def render_png(font_bytes, family, version):
    image = Image.new('RGB', (1800, 1600), '#f7f2e7')
    draw = ImageDraw.Draw(image)

    def text(x, y, value, size):
        font = ImageFont.truetype(io.BytesIO(font_bytes), size)
        draw.text((x, y), value, font=font, fill='#173e36')

    for x, y, value, size in [
        (100, 80, '鳥', 230), (350, 95, '花', 210),
        (580, 80, '虫', 230), (850, 95, '月', 210),
        (110, 390, '山川草木  天地日月', 130),
        (110, 620, 'あいうえお  アイウエオ', 100),
        (110, 800, 'はるの山  風と鳥の声', 110),
        (110, 1010, 'ABC  abc  0123456789', 100),
        (110, 1200, '「花の色、空の青。」', 100),
    ]:
        text(x, y, value, size)
    draw.text((115, 1480), f'{family.upper()} / ORIGINAL IMAGE-GENERATED GLYPHS / {version}',
              font=ImageFont.load_default(size=26), fill='#7b756a')
    image.save(ROOT / 'output/specimen.png')


def main():
    font_bytes = (ROOT / 'output/ChochutenKacho-Regular.ttf').read_bytes()
    font = TTFont(io.BytesIO(font_bytes))
    cmap = font.getBestCmap()
    manifest = json.loads((ROOT / 'sources/manifest.json').read_text())
    family = font['name'].getDebugName(1)
    japanese_name = font['name'].getName(1, 3, 1, 0x411)
    display_family = japanese_name.toUnicode() if japanese_name else family
    version = font['name'].getDebugName(5).removeprefix('Version ')
    groups = character_groups(cmap, manifest)
    vertical = vertical_forms(font, cmap)
    definitions, sections = render_catalog(font, cmap, groups, vertical)
    styles = Template((TEMPLATES / 'specimen.css').read_text()).substitute(
        font_data=base64.b64encode(font_bytes).decode('ascii'),
        sample_size=SAMPLE_SIZE, catalog_size=CATALOG_SIZE,
    )
    page = Template((TEMPLATES / 'specimen.html').read_text()).substitute(
        display_family=html.escape(display_family), family=html.escape(family),
        version=html.escape(version), font_hash=hashlib.sha256(font_bytes).hexdigest(),
        character_count=len(cmap), glyph_count=len(font.getGlyphOrder()),
        vertical_count=len(vertical), sample_size=SAMPLE_SIZE,
        styles=styles, definitions=definitions, sections=sections,
        script=(TEMPLATES / 'specimen.js').read_text(),
    )
    (ROOT / 'output/specimen.html').write_text(page, encoding='utf-8')
    render_png(font_bytes, family, version)
    print(f'Specimen: {len(cmap)} characters, {len(vertical)} vertical forms, version {version}')


if __name__ == '__main__':
    main()

"""Create a separate font family with 150% glyph height and unchanged width."""
from pathlib import Path
import json
from fontTools.ttLib import TTFont
from fontTools.misc.roundTools import otRound
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.roundingPen import RoundingPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.t2CharStringPen import T2CharStringPen
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.boundsPen import BoundsPen
import uharfbuzz as hb
from metadata import apply_metadata, verify_metadata

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'output'
QA = ROOT / 'qa'
SCALE = 1.5


def scaled(value):
    return otRound(value * SCALE)


def verify_widths(font):
    cmap = font.getBestCmap()
    # All encoded non-Latin spacing glyphs, including Japanese punctuation,
    # fullwidth ASCII, small kana and ideographic space, must be one em wide.
    fullwidth = {cp: gn for cp, gn in cmap.items()
                 if cp not in (0x20, 0xa0, 0x3099, 0x309a)
                 and not 0x21 <= cp <= 0x7e}
    assert fullwidth
    assert {font['hmtx'][gn][0] for gn in fullwidth.values()} == {1000}
    assert all(font['hmtx'][cmap[cp]][0] == 0 for cp in (0x3099, 0x309a))
    alternates = [gn for gn in font.getGlyphOrder() if gn.endswith('.vert')]
    assert len(alternates) == 24
    assert all(font['hmtx'][gn][0] == 1000 for gn in alternates)
    return {'fullwidth_characters': len(fullwidth), 'advance_width': 1000,
            'vertical_alternates': len(alternates), 'combining_marks_width': 0}


reports = {}
for ext in ('ttf', 'otf'):
    original = TTFont(OUT / f'ChochutenKacho-Regular.{ext}')
    source_widths = verify_widths(original)
    font = TTFont(OUT / f'ChochutenKacho-Regular.{ext}')
    glyph_set = font.getGlyphSet()
    drawn = {}
    for name in font.getGlyphOrder():
        pen = TTGlyphPen(None) if ext == 'ttf' else T2CharStringPen(font['hmtx'][name][0], None)
        glyph_set[name].draw(TransformPen(RoundingPen(pen), (1, 0, 0, SCALE, 0, 0)))
        drawn[name] = pen.glyph() if ext == 'ttf' else pen.getCharString(optimize=False)
    if ext == 'ttf':
        for name, glyph in drawn.items():
            font['glyf'][name] = glyph
    else:
        top = font['CFF '].cff.topDictIndex[0]
        for name, charstring in drawn.items():
            charstring.private = top.Private
            charstring.globalSubrs = font['CFF '].cff.GlobalSubrs
            top.CharStrings[name] = charstring
        font['CFF '].cff.fontNames = ['ChochutenKacho-Tall150-Regular']
        top.FamilyName = 'Chochuten Kacho Tall150'
        top.FullName = 'Chochuten Kacho Tall150 Regular'
    for name, (advance, bearing) in list(font['vmtx'].metrics.items()):
        source_set = original.getGlyphSet()
        bounds = BoundsPen(source_set)
        source_set[name].draw(bounds)
        top = bounds.bounds[3] if bounds.bounds else 0
        font['vmtx'][name] = (scaled(advance), scaled(top + bearing) - scaled(top))
    for field in ('ascent', 'descent', 'lineGap'):
        setattr(font['hhea'], field, scaled(getattr(font['hhea'], field)))
    os2 = font['OS/2']
    for field in ('sTypoAscender', 'sTypoDescender', 'sTypoLineGap',
                  'usWinAscent', 'usWinDescent', 'sxHeight', 'sCapHeight',
                  'ySubscriptYSize', 'ySubscriptYOffset', 'ySuperscriptYSize',
                  'ySuperscriptYOffset', 'yStrikeoutSize', 'yStrikeoutPosition'):
        if hasattr(os2, field):
            setattr(os2, field, scaled(getattr(os2, field)))
    for field in ('underlinePosition', 'underlineThickness'):
        setattr(font['post'], field, scaled(getattr(font['post'], field)))
    if 'VORG' in font:
        vorg = font['VORG']
        vorg.defaultVertOriginY = scaled(vorg.defaultVertOriginY)
        vorg.VOriginRecords = {gn: scaled(y) for gn, y in vorg.VOriginRecords.items()}
    for record in list(font['name'].names):
        if record.nameID in (1, 2, 3, 4, 6, 16, 17):
            font['name'].removeNames(nameID=record.nameID, platformID=record.platformID,
                                     platEncID=record.platEncID, langID=record.langID)
    version = original['name'].getDebugName(5)
    for language, family, style in [(0x409, 'Chochuten Kacho Tall150', 'Regular'),
                                    (0x411, '鳥虫篆 花鳥 縦長150', '標準')]:
        for name_id, value in {1: family, 2: style, 3: f'ChochutenKacho-Tall150-Regular-{version}',
                               4: f'{family} {style}', 6: 'ChochutenKacho-Tall150-Regular',
                               16: family, 17: style}.items():
            font['name'].setName(value, name_id, 3, 1, language)
    apply_metadata(font, tall=True)
    path = OUT / f'ChochutenKacho-Tall150-Regular.{ext}'
    font.save(path)
    result = TTFont(path)
    verify_metadata(result)
    assert result['head'].unitsPerEm == original['head'].unitsPerEm == 1000
    assert result.getBestCmap() == original.getBestCmap()
    assert result['hmtx'].metrics == original['hmtx'].metrics
    assert verify_widths(result) == source_widths
    assert result['OS/2'].ulCodePageRange1 & (1 << 17)
    assert result['name'].getName(1, 3, 1, 0x411).toUnicode() == '鳥虫篆 花鳥 縦長150'
    # Compare every outline point after saving/reopening, not just glyph bounds.
    src, dst = original.getGlyphSet(), result.getGlyphSet()
    for name in original.getGlyphOrder():
        expected, actual = RecordingPen(), RecordingPen()
        src[name].draw(TransformPen(RoundingPen(expected), (1, 0, 0, SCALE, 0, 0)))
        dst[name].draw(actual)
        assert expected.value == actual.value, (ext, name)
    shaping = hb.Font(hb.Face(path.read_bytes()))
    shaping.scale = (1000, 1000)
    hb.ot_font_set_funcs(shaping)
    for direction in ('ltr', 'ttb'):
        buf = hb.Buffer()
        buf.add_str('「花の色、空の青。」')
        buf.direction, buf.script, buf.language = direction, 'Hani', 'ja'
        hb.shape(shaping, buf)
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            assert info.codepoint != 0
            assert (pos.x_advance, pos.y_advance) == ((1000, 0) if direction == 'ltr' else (0, -1500))
            if direction == 'ttb':
                assert (pos.x_offset, pos.y_offset) == (-500, -1350)
    reports[ext] = {'original': source_widths, 'tall150': verify_widths(result),
                    'glyphs_point_checked': len(result.getGlyphOrder()),
                    'horizontal_metrics_unchanged': True, 'y_scale': SCALE,
                    'rounding': 'OpenType nearest integer, ties towards positive infinity',
                    'horizontal_and_vertical_shaping': 'passed'}
QA.mkdir(exist_ok=True)
(QA / 'stretch-validation.json').write_text(json.dumps(reports, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(reports, ensure_ascii=False, indent=2))

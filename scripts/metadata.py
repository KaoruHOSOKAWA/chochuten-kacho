"""OpenType language/style declarations for the limited-character display fonts."""
from fontTools.ttLib import newTable

DESCRIPTION = '鳥虫篆を題材にした日本語装飾書体。漢字288字を含む686文字を収録した限定文字フォントです。一般的な日本語文章の全漢字には対応していません。ラテン文字は基本ASCIIを中心とし、アクセント付き文字は収録していません。'
LICENSE = 'CC0 1.0 Universal。法令上可能な範囲で、本フォントの著作権および関連する権利を放棄しています。詳細は同梱のLICENSE.txtおよび https://creativecommons.org/publicdomain/zero/1.0/ を参照してください。'


def apply_metadata(font, tall=False):
    # ScriptLangTags declare script capabilities, not full character coverage.
    font['meta'] = newTable('meta')
    font['meta'].data = {'dlng': 'Jpan', 'slng': 'Jpan, Latn'}
    font['OS/2'].fsSelection = 0x0040
    # Keep the Japanese classification; do not claim Windows-1252 coverage.
    font['OS/2'].ulCodePageRange1 = 1 << 17
    font['OS/2'].ulCodePageRange2 = 0
    font['name'].setName(DESCRIPTION + (' 横幅を維持し縦方向を1.5倍にした縦長150版。' if tall else ''), 10, 3, 1, 0x411)
    font['name'].setName(LICENSE, 13, 3, 1, 0x411)
    # Restore legacy Macintosh English names as well as Windows names.
    for name_id in (1, 2, 3, 4, 6, 16, 17):
        record = font['name'].getName(name_id, 3, 1, 0x409)
        assert record is not None
        font['name'].setName(record.toUnicode(), name_id, 1, 0, 0)


def verify_metadata(font):
    assert font['meta'].data == {'dlng': 'Jpan', 'slng': 'Jpan, Latn'}
    assert font['OS/2'].fsSelection == 0x0040
    assert font['OS/2'].ulCodePageRange1 == 1 << 17
    assert font['OS/2'].ulCodePageRange2 == 0
    for name_id in (10, 13):
        assert font['name'].getName(name_id, 3, 1, 0x411).toUnicode()
    for name_id in (1, 2, 3, 4, 6, 16, 17):
        assert font['name'].getName(name_id, 1, 0, 0).toUnicode() == font['name'].getName(name_id, 3, 1, 0x409).toUnicode()

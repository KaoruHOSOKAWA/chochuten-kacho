![鳥虫篆 花鳥の使用見本](output/specimen.png)

# 鳥虫篆 花鳥 — Chochuten Kacho 1.004

鳥の嘴・目・尾と虫のような曲線を筆画に織り込んだ、鳥虫篆を題材にした和文装飾フォントです。

**制作：GPT-6.1 Sol**。すべての可視字形の元画像を画像生成で作成し、輪郭化・フォント化しました。

## ダウンロード

[GitHub Releases](https://github.com/KaoruHOSOKAWA/chochuten-kacho/releases/tag/v1.004)から、OTF・TTF・元画像とソースを含む配布ZIPをダウンロードできます。

フォント名は「鳥虫篆 花鳥 / Chochuten Kacho」です。OTFかTTFのどちらか一方をインストールしてください。

[試し打ち・字形一覧](output/specimen.html) / [収録文字一覧](output/characters.txt)

## 収録範囲

- 小学1年漢字80字・小学2年漢字160字と、追加漢字48字。
- ひらがな・カタカナ（濁音・半濁音・小書き・旧かなを含む）。
- 英数字・全角英数字・和文約物・記号・空白・結合濁点と半濁点。

686のUnicode文字、縦組み用24字形を含む711グリフを収録。縦書きでは約物の回転と句読点の右上への移動に対応します。

## ライセンス

フォント・元画像・独自ソースコードは **[CC0 1.0 Universal](LICENSE)** です。

## Dockerでビルド

```sh
docker compose build
docker compose run --rm font
```

生成済み元画像からビルドし、OTF・TTF・見本・配布ZIPを `output/` に出力します。

通常版に加え、横幅を変えずにベースライン基準で縦座標を1.5倍にした
「鳥虫篆 花鳥 縦長150 / Chochuten Kacho Tall150」も生成します。
ファイル名は `ChochutenKacho-Tall150-Regular.ttf` / `.otf` です。
行間と縦書きの送りも高さに合わせて拡張しています。
通常版の生成後、`python scripts/stretch.py` で個別に再生成できます。

全角588文字と縦組み用24字形の送り幅は、通常版・縦長版とも1000 unitsです。
結合濁点・半濁点は重ね合わせ用のため0です。
`qa/stretch-validation.json` に全角送り幅・全711字形の座標変換・組版の検証結果を記録します。

## 言語メタデータと収録範囲

`meta.dlng=Jpan`、`meta.slng=Jpan, Latn` は日本語・ラテン文字の文字体系への対応を宣言します。全文字の収録を保証する指定ではありません。本書体は漢字288字を含む686文字の限定文字フォントで、基本ASCII以外のラテン文字も限定されます。一般文章ではフォールバックが必要です。Fontconfigの`ja`判定に必要な文字集合は満たしていないため、このメタデータ追加によって`fc-scan`で`ja`が表示されるとは限りません。

通常版・縦長版ともRegular属性を設定し、未収録のアクセント付き文字を含むWindows-1252対応フラグは設定しません。日本語の説明・CC0説明、WindowsおよびMacintoshの英語名称を収録しています。`GPOS`・`locl`・`ltag`は追加していません。既存の`JAN `・`ccmp`・`vert`・`vrt2`は維持します。

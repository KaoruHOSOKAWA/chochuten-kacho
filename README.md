![鳥虫篆 花鳥の使用見本](output/specimen.png)

# 鳥虫篆 花鳥 — Chochuten Kacho 1.002

鳥の嘴・目・尾と虫のような曲線を筆画に織り込んだ、鳥虫篆を題材にした和文装飾フォントです。

**制作：GPT-6.1 Sol**。すべての可視字形の元画像を画像生成で作成し、輪郭化・フォント化しました。

## ダウンロード

[GitHub Releases](https://github.com/KaoruHOSOKAWA/chochuten-kacho/releases/tag/v1.002)から、OTF・TTF・元画像とソースを含む配布ZIPをダウンロードできます。

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


## 開発者向け

### 要求定義
- RFCを日本語に翻訳し、その訳が正しいのか判断しやすいように表示したい
- 見出しを大きくしたり、サンプルコードは等幅フォントで表示するなど、RFC原文よりも読みやすくしたい

### 要件定義
- レイアウト
  - 原文は左側、対訳は右側に表示すること
  - 表示はレスポンシブデザインにする。PC画面で見る場合は対訳が左右に並び、スマホ画面で見る場合は対訳が上下に並ぶように表示すること
- 内容
  - 文章のみ翻訳し、図や表やサンプルコードはそのまま表示すること
  - 文章がページ区切りで分割されていても1つの段落として翻訳すること
  - インデントの深さも表示に反映させること
  - 箇条書き（o + * - など）の記号はそのまま表示すること（翻訳時は箇条書き記号より後の文字列だけを翻訳する）
  - 表題（1.2.～ など）は見出しとして文字を大きくすること
  - 目次から各セクションへのリンクを貼る
  - 本文中の[RFCxxxx]から別RFCへのリンクを貼る
- ヘッダー
  - 原本（英語RFC）へのリンクを配置し、スクロールしても常に表示すること
  - モード切り替えのボタンを配置し、ダークモードへ切り替えられること
  - 廃止されたRFCの場合、廃止されたことと修正版RFCへのリンクを表示すること (例：RFC2246, RFC2616)
  - RFCのステータス（Proposed Standard / Internet Standard など）を表示すること
  - RFCを発行したWG（ワーキンググループ）を表示すること


### 動作環境
Python3 + Selenium (FireFox) on Windows / MacOS / Ubuntu (headless)

requests, lxml, beautifulsoup4, Mako, tqdm, seleniumなどのライブラリが実行に必要のためインストールしてください。Windowsの場合は、py -m pip に読み替えてください。
```
pip3 install -r requirements.txt
```

加えてSeleniumを動かすために以下のツールが実行に必要です。
- **Windows**: FireFox のサイトから geckodriver.exe をダウンロードし、src/trans_rfc.py から呼び出せるように環境変数 WEBDRIVER_EXE_PATH に exe のパスを設定ください。
- **Linux (Ubuntu)** の場合は、以下のパッケージをインストールください。
    ```
    sudo apt install python3-pip firefox xdg-utils
    sudo pip install selenium
    ```

### 実行コマンド例

**注意：翻訳処理は非常に時間がかかります。1個のRFCを翻訳するのに短いものは5分、長いものは30分〜1時間程度かかります。**
開発初期には複数のインスタンスを起動して同時並行で24時間回し続けたのを半年くらいしていました。

- **取得・翻訳・生成**

    ```bash
    python3 main.py --rfc 1234          # RFC1234を翻訳する（取得+翻訳+HTML生成）
    python3 main.py --rfc 1234 --fetch  # RFCの取得だけ
    python3 main.py --rfc 1234 --trans  # RFCの翻訳だけ
    python3 main.py --rfc 1234 --make   # HTMLの生成だけ
    python3 main.py --begin 2220 --end 10000         # RFC2220〜10000を翻訳する
    python3 main.py --make --begin 2220 --end 10000  # RFC2220〜10000のHTMLを生成する
    python3 main.py --begin 8000 --only-first  # RFC8000以降の未翻訳RFCを1つ選択して翻訳する
    ```

- **トップページの生成**

    htmlフォルダ内に存在するRFCファイルの一覧から、トップページを作成します。
    ```bash
    python3 main.py --make-index  # インデックス（目次）ページの作成
    ```

- **RFCのステータス・WGの一覧作成**

    RFCのステータス・WGの一覧を作成して、JSONに保存するためのコマンドです。

    ```bash
    python3 main.py --fetch-status
    ```

- **RFC Draftの翻訳**

    例えば、TLS Encrypted Client Hello (Draft版) である https://datatracker.ietf.org/doc/draft-ietf-tls-esni/ を翻訳したい場合は、以下のコマンドを実行します。
    ```bash
    python3 main.py --draft draft-ietf-tls-esni-14
    python3 main.py --make-index-draft  # インデックスページの作成
    ```

- **RFCの要約作成**

    ```bash
    python3 main.py --summarize --make --rfc 9446  # 指定したRFCのみ
    python3 main.py --summarize --make --force --begin 9600 --end 9700  # 範囲指定
    ```

生成物：

| ファイルパス | 説明 | 生成元プログラム |
|-----------|-----|--------------|
| html/data-rfc-list.json | 廃止RFC・WGの一覧 | fetch_wg.py (取得)
| data/N000/rfcNXXX.json | 段落区切りの文書 | fetch_rfc.py（取得）
| data/N000/rfcNXXX-trans.json | 各文章の翻訳を付与した情報 | trans_rfc.py（翻訳）
| html/rfcNXXX.html | 原文と翻訳を並べて表示するHTML | make_html.py（生成）
| html/index.html | トップページの生成 | make_index.py (生成)
| data/draft/draft-*.json | 段落区切りの文書 | fetch_rfc.py（取得）
| data/draft/draft-*-trans.json | 各文章の翻訳を付与した情報 | trans_rfc.py（翻訳）
| html/draft/draft-*.html | RFCドラフトの原文と翻訳を並べて表示するHTML | make_html.py（生成）
| html/draft/index.html | RFCドラフト一覧のトップページHTML | make_html.py（生成）


### 翻訳結果確認
ローカルで成果物の確認：
```bash
python3 -m http.server
# localhost:8000/htmlにアクセス
```

### 単体テスト
```bash
python3 -m unittest discover -s tests -p "test_*.py"
```
特定のテストのみ実施したい場合
```
python3 -m unittest tests.test_fetch_rfc.TestFetchRfcSectionTitle.test_section_title
```

### Draft版の全RFCのHTMLを再作成する

```bash
find data/draft -name '*' -type f -exec /bin/bash -c '/opt/homebrew/bin/python3 main.py --draft $(basename {} -trans.json) --make' \;
python main.py --make-index-draft
```

### その他

#### 図表・ソースコードをJSONへ変換する
RFCを解析した結果、本来プログラムとして解釈すべき部分を文章として解釈してしまった場合、プログラムのインデントを削除してJSON化するツール：
[https://tex2e.github.io/rfc-translater/html/format.html](https://tex2e.github.io/rfc-translater/html/format.html)



<!--
### Figs

各RFCから図のみを集めて公開するサイト「RFC Figs」について（現在、更新予定はありません）

```bash
# 1000個のRFC毎に図を集め、JSONファイルで保存する
python3 figs/collect_figures.py --begin 0000 --end 0999 -w figs/data/0000.json
...
python3 figs/collect_figures.py --begin 7000 --end 7999 -w figs/data/7000.json

# JSONをHTMLに変換する
python3 figs/make_html.py 0000
...
python3 figs/make_html.py 7000

# インデックスページの作成
python3 figs/make_index.py
```
-->

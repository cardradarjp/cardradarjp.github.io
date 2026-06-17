# CardRadar 更新手順

## 通常の最新版更新

```bash
git checkout main
git pull origin main

python -m py_compile test.py
python test.py
python test.py --rebuild-html
```

## 更新後にコミットするファイル

基本的に以下を確認してコミットする。

* data.json
* osaka-nihonbashi.html
* stores/*.html

## コミットに含めないもの

* userdata/
* __pycache__/
* 不要なログファイル
* 一時ファイル

## 公開確認URL

```text
https://cardradarjp.github.io/osaka-nihonbashi.html
```

キャッシュが残る場合は、末尾に `?v=任意の文字列` を付けて確認する。

例：

```text
https://cardradarjp.github.io/osaka-nihonbashi.html?v=check1
```

## 注意

UI修正だけの場合は、通常取得の `python test.py` は実行しない。
その場合は以下だけで確認する。

```bash
python -m py_compile test.py
python test.py --rebuild-html
```

from playwright.sync_api import sync_playwright
import time
import re
import json
import html as html_lib
from datetime import datetime
from pathlib import Path
from urllib.parse import quote


USER_DATA_DIR = "userdata"
Path(USER_DATA_DIR).mkdir(exist_ok=True)

MAX_POSTS_PER_SOURCE = 3
CHECK_POSTS_PER_SOURCE = 60


TYPE_META = {
    "x_post_single": {
        "label": "シングル買取",
        "en": "SINGLE",
        "desc": "カード単品の買取表",
    },
    "x_post_box": {
        "label": "BOX買取",
        "en": "BOX",
        "desc": "未開封BOX・パック買取",
    },
    "x_post_fixed": {
        "label": "定額買取",
        "en": "FIXED PRICE",
        "desc": "ノーマル・RR・ARなどのまとめ買取",
    },
    "x_post_psa": {
        "label": "PSA買取",
        "en": "PSA",
        "desc": "PSA・鑑定品の買取",
    },
    "official_price_list": {
        "label": "公式Web買取表",
        "en": "OFFICIAL LIST",
        "desc": "公式サイト掲載の買取表",
    },
    "market_price_link": {
        "label": "相場確認",
        "en": "MARKET PRICE",
        "desc": "メルカリ等の相場確認リンク",
    },
}


def x_search_url(account, words):
    query = f"from:{account} {words} filter:images"
    return "https://x.com/search?q=" + quote(query) + "&src=typed_query&f=live"


SINGLE_WORDS = "(ポケカ OR ポケモンカード OR Pokemon) (買取 OR 高価買取 OR 買取表 OR WANTED OR 募集)"
BOX_WORDS = "(ポケカ OR ポケモンカード OR Pokemon) (BOX OR box OR 未開封 OR シュリンク OR パック OR カートン) (買取 OR 高価買取 OR 募集)"
FIXED_WORDS = "(ポケカ OR ポケモンカード OR Pokemon) (定額 OR 一律 OR まとめ買取 OR 最低保証 OR ノーマル OR RR OR AR OR 汎用 OR ストレージ) (買取 OR 募集)"
PSA_WORDS = "(ポケカ OR ポケモンカード OR Pokemon) (PSA OR PSA10 OR PSA9 OR 鑑定品 OR ARS OR BGS OR 鑑定) (買取 OR 高価買取 OR 募集)"


SOURCES = [
    {
        "source_type": "x_post_single",
        "name": "ドラスタ オタロード中央",
        "brand": "ドラゴンスター",
        "brand_id": "dragonstar",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "ドラゴンスター オタロード中央店のポケカシングル買取情報。",
        "url": x_search_url("ds_otaroad_chuo", SINGLE_WORDS),
    },
    {
        "source_type": "x_post_single",
        "name": "ドラスタ 日本橋本店",
        "brand": "ドラゴンスター",
        "brand_id": "dragonstar",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "ドラゴンスター 日本橋本店のポケカシングル買取情報。",
        "url": x_search_url("ds_nipponbashi", SINGLE_WORDS),
    },
    {
        "source_type": "x_post_single",
        "name": "ドラスタ 日本橋2号店",
        "brand": "ドラゴンスター",
        "brand_id": "dragonstar",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "ドラゴンスター 日本橋2号店のポケカ買取表・WANTED情報。",
        "url": x_search_url("ds_nipponbashi2", SINGLE_WORDS),
    },
    {
        "source_type": "x_post_single",
        "name": "ドラスタ 日本橋3号店",
        "brand": "ドラゴンスター",
        "brand_id": "dragonstar",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "ドラゴンスター 日本橋3号店のポケカシングル買取情報。",
        "url": x_search_url("ds_nipponbashi3", SINGLE_WORDS),
    },
    {
        "source_type": "x_post_single",
        "name": "ドラスタ なんさん通り店",
        "brand": "ドラゴンスター",
        "brand_id": "dragonstar",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "ドラゴンスター なんさん通り店のポケカ買取情報。",
        "url": x_search_url("ds_namba_nansan", SINGLE_WORDS),
    },
    {
        "source_type": "x_post_single",
        "name": "晴れる屋2なんば",
        "brand": "晴れる屋2",
        "brand_id": "hareruya2",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "晴れる屋2なんば店のポケカ買取表。",
        "url": x_search_url("hareruya2namba", SINGLE_WORDS),
    },
    {
        "source_type": "x_post_single",
        "name": "カードラボなんば店",
        "brand": "カードラボ",
        "brand_id": "cardlabo",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "カードラボなんば店のポケカ買取情報。",
        "url": x_search_url("namba_clabo", SINGLE_WORDS),
    },
    {
        "source_type": "x_post_single",
        "name": "カードラボ大阪日本橋店",
        "brand": "カードラボ",
        "brand_id": "cardlabo",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "カードラボ大阪日本橋店のポケカ買取情報。",
        "url": x_search_url("nipponbashi_lab", SINGLE_WORDS),
    },
    {
        "source_type": "x_post_single",
        "name": "GIRAFULLなんば店",
        "brand": "GIRAFULL",
        "brand_id": "girafull",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "GIRAFULLなんば店のポケカ買取情報。",
        "url": x_search_url("GIRAFULL_Namba", SINGLE_WORDS),
    },
    {
        "source_type": "x_post_single",
        "name": "GIRAFULL大阪日本橋店",
        "brand": "GIRAFULL",
        "brand_id": "girafull",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "GIRAFULL大阪日本橋店のポケカ買取情報。",
        "url": x_search_url("girafull_o_n", SINGLE_WORDS),
    },

    {
        "source_type": "x_post_single",
        "name": "アムタフ シングル買取",
        "brand": "アムタフ",
        "brand_id": "amtaf",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "アムタフのポケカシングル買取情報。",
        "url": x_search_url("AMTAF_SHOP", SINGLE_WORDS),
    },
    {
        "source_type": "x_post_box",
        "name": "アムタフ BOX買取",
        "brand": "アムタフ",
        "brand_id": "amtaf",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "アムタフのポケカ未開封BOX・パック買取情報。",
        "url": x_search_url("AMTAF_SHOP", BOX_WORDS),
    },
    {
        "source_type": "x_post_fixed",
        "name": "アムタフ 定額買取",
        "brand": "アムタフ",
        "brand_id": "amtaf",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "アムタフの定額買取・まとめ買取情報。",
        "url": x_search_url("AMTAF_SHOP", FIXED_WORDS),
    },
    {
        "source_type": "x_post_single",
        "name": "GOTCHA! シングル買取",
        "brand": "GOTCHA!",
        "brand_id": "gotcha",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "GOTCHA!のポケカシングル買取情報。",
        "url": x_search_url("cardshop_gotcha", SINGLE_WORDS),
    },
    {
        "source_type": "x_post_box",
        "name": "GOTCHA! BOX買取",
        "brand": "GOTCHA!",
        "brand_id": "gotcha",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "GOTCHA!のポケカ未開封BOX・パック買取情報。",
        "url": x_search_url("cardshop_gotcha", BOX_WORDS),
    },
    {
        "source_type": "x_post_single",
        "name": "KURO シングル買取",
        "brand": "KURO",
        "brand_id": "kuro",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "KUROのポケカシングル買取情報。",
        "url": x_search_url("kuro_tcg", SINGLE_WORDS),
    },
    {
        "source_type": "x_post_box",
        "name": "KURO BOX買取",
        "brand": "KURO",
        "brand_id": "kuro",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "KUROのポケカ未開封BOX・パック・カートン買取情報。",
        "url": x_search_url("kuro_tcg", BOX_WORDS),
    },
    {
        "source_type": "x_post_single",
        "name": "買取ミミ シングル買取",
        "brand": "買取ミミ",
        "brand_id": "mimi",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "買取ミミのポケカシングル買取情報。",
        "url": x_search_url("mimi_kaitori", SINGLE_WORDS),
    },
    {
        "source_type": "x_post_fixed",
        "name": "買取ミミ 定額買取",
        "brand": "買取ミミ",
        "brand_id": "mimi",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "買取ミミの定額買取・まとめ買取情報。",
        "url": x_search_url("mimi_kaitori", FIXED_WORDS),
    },

    {
        "source_type": "official_price_list",
        "name": "Clove Base",
        "brand": "Clove",
        "brand_id": "clove",
        "area": "公式Web",
        "area_id": "official-web",
        "description": "ポケモンカードの公式Web買取表。",
        "official_url": "https://base.clove.jp/prices/pokemon",
    },
    {
        "source_type": "official_price_list",
        "name": "フルアヘッド",
        "brand": "フルアヘッド",
        "brand_id": "fullahead",
        "area": "公式Web",
        "area_id": "official-web",
        "description": "ポケカを含むTCGの公式Web買取表。",
        "official_url": "https://fullahead-buy.com/",
    },
    {
        "source_type": "market_price_link",
        "name": "メルカリ ポケカ相場",
        "brand": "メルカリ",
        "brand_id": "mercari",
        "area": "相場確認",
        "area_id": "market",
        "description": "メルカリでポケカ相場を確認する検索リンク。",
        "official_url": "https://jp.mercari.com/search?keyword=%E3%83%9D%E3%82%B1%E3%82%AB",
    },
    {
        "source_type": "market_price_link",
        "name": "メルカリ BOX相場",
        "brand": "メルカリ",
        "brand_id": "mercari",
        "area": "相場確認",
        "area_id": "market",
        "description": "メルカリでポケカ未開封BOX相場を確認する検索リンク。",
        "official_url": "https://jp.mercari.com/search?keyword=%E3%83%9D%E3%82%B1%E3%82%AB%20BOX%20%E6%9C%AA%E9%96%8B%E5%B0%81",
    },
]


def is_target_post(text, source_type):
    pokemon_words = ["ポケカ", "ポケモンカード", "Pokemon", "pokemon"]
    buy_words = ["買取", "高価買取", "買取表", "WANTED", "募集"]

    if not any(w in text for w in pokemon_words):
        return False
    if not any(w in text for w in buy_words):
        return False

    ng_words = [
        "大会", "優勝", "抽選", "販売開始", "BOX争奪戦", "争奪戦",
        "ワンピース", "遊戯王", "デュエマ", "MTG", "ヴァイス"
    ]
    if any(w in text for w in ng_words):
        return False

    if source_type == "x_post_box":
        box_words = ["BOX", "box", "未開封", "シュリンク", "パック", "カートン"]
        box_ng_words = ["BOX買取以外", "BOX以外", "ボックス以外", "未開封BOX以外", "BOX対象外"]
        single_words = ["SAR", "SR", "UR", "HR", "CSR", "CHR", "AR", "SA", "ex", "EX"]

        if not any(w in text for w in box_words):
            return False
        if any(w in text for w in box_ng_words):
            return False
        if sum(1 for w in single_words if w in text) >= 4:
            return False
        return True

    if source_type == "x_post_fixed":
        fixed_words = ["定額", "一律", "まとめ買取", "最低保証", "ノーマル", "RR", "AR", "ストレージ"]
        return any(w in text for w in fixed_words)

    if source_type == "x_post_psa":
        psa_words = ["PSA", "PSA10", "PSA9", "鑑定品", "鑑定", "ARS", "BGS"]
        return any(w in text for w in psa_words)

    return True


def clean_tweet_text(text):
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("@"):
            continue
        if line in ["·", "さらに表示"]:
            continue
        lines.append(line)

    summary = " ".join(lines)
    return summary[:220] + "..." if len(summary) > 220 else summary


def get_status_url(tweet):
    links = tweet.locator("a")
    for i in range(links.count()):
        href = links.nth(i).get_attribute("href")
        if not href:
            continue
        if "/status/" in href and "/photo/" not in href and "/analytics" not in href:
            return "https://x.com" + href if href.startswith("/") else href
    return None


def get_status_id(url):
    match = re.search(r"/status/(\d+)", url)
    return int(match.group(1)) if match else 0


def get_image_urls(tweet):
    urls = []
    images = tweet.locator("img")
    for i in range(images.count()):
        src = images.nth(i).get_attribute("src")
        if not src:
            continue
        if "pbs.twimg.com/media" in src:
            src = src.replace("name=small", "name=large").replace("name=medium", "name=large")
            if src not in urls:
                urls.append(src)
    return urls


def unique_values(key, label_key):
    values = []
    for s in SOURCES:
        if not any(v["id"] == s[key] for v in values):
            values.append({"id": s[key], "label": s[label_key]})
    return values


def search_text(source):
    return " ".join([
        source.get("name", ""),
        source.get("brand", ""),
        source.get("area", ""),
        TYPE_META[source["source_type"]]["label"],
        TYPE_META[source["source_type"]]["en"],
        source.get("description", ""),
    ])


def build_html(posts_by_source, updated_at):
    all_items = []

    for source in SOURCES:
        source_id = source["name"] + "_" + source["source_type"]
        posts = posts_by_source.get(source_id, [])
        all_items.append((source, posts))

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CardRadar｜ポケカ買取情報を探す</title>
<meta name="description" content="CardRadarは、ポケカのシングル買取、BOX買取、定額買取、PSA買取、公式Web買取表、相場確認リンクをまとめて探せるサイトです。">

<style>
* {{
  box-sizing: border-box;
}}

html {{
  scroll-behavior: smooth;
}}

body {{
  margin: 0;
  background: #050505;
  color: #f5f5f5;
  font-family: "Noto Serif JP", "Yu Mincho", "Hiragino Mincho ProN", "Times New Roman", serif;
}}

body::before {{
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  background:
    radial-gradient(circle at 16% 16%, rgba(255,255,255,.17), transparent 18%),
    radial-gradient(circle at 22% 26%, rgba(255,255,255,.06), transparent 24%),
    linear-gradient(90deg, rgba(255,255,255,.035), transparent 35%),
    repeating-linear-gradient(0deg, rgba(255,255,255,.015), rgba(255,255,255,.015) 1px, transparent 1px, transparent 5px);
  opacity: .75;
  z-index: -2;
}}

body::after {{
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(90deg, transparent 0%, transparent 70%, rgba(255,255,255,.035) 73%, transparent 76%),
    linear-gradient(90deg, transparent 0%, transparent 78%, rgba(255,255,255,.03) 80%, transparent 84%),
    linear-gradient(180deg, #080808 0%, #030303 100%);
  opacity: .9;
  z-index: -3;
}}

.hero {{
  min-height: 620px;
  padding: 46px 7vw 32px;
  position: relative;
  overflow: hidden;
}}

.top-nav {{
  display: flex;
  justify-content: flex-end;
  gap: 42px;
  font-size: 13px;
  letter-spacing: .28em;
  color: rgba(255,255,255,.84);
}}

.brand-block {{
  margin-top: 70px;
  display: grid;
  grid-template-columns: 220px 1fr;
  align-items: center;
  gap: 48px;
}}

.logo-mark {{
  font-size: 132px;
  letter-spacing: -.18em;
  line-height: .82;
  font-weight: 400;
  text-shadow: 0 0 28px rgba(255,255,255,.18);
}}

.brand-name {{
  font-size: 42px;
  letter-spacing: .46em;
  font-weight: 400;
}}

.brand-sub {{
  margin-top: 14px;
  color: rgba(255,255,255,.52);
  letter-spacing: .48em;
  font-size: 12px;
}}

.copy {{
  margin-top: 46px;
  line-height: 2.3;
  letter-spacing: .22em;
  color: rgba(255,255,255,.92);
}}

.updated {{
  margin-top: 24px;
  color: rgba(255,255,255,.45);
  font-size: 12px;
  letter-spacing: .18em;
}}

.find-title {{
  margin-top: 82px;
  font-size: 14px;
  letter-spacing: .16em;
  color: rgba(255,255,255,.86);
}}

.type-tabs {{
  margin-top: 14px;
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  border: 1px solid rgba(255,255,255,.14);
  background: rgba(0,0,0,.28);
}}

.type-tab {{
  border: 0;
  border-right: 1px solid rgba(255,255,255,.13);
  background: transparent;
  color: white;
  padding: 22px 14px;
  cursor: pointer;
  text-align: left;
}}

.type-tab.active {{
  background: rgba(255,255,255,.075);
  box-shadow: inset 0 0 22px rgba(255,255,255,.09);
}}

.type-tab span {{
  display: block;
  font-size: 15px;
  letter-spacing: .12em;
}}

.type-tab small {{
  display: block;
  margin-top: 7px;
  color: rgba(255,255,255,.45);
  letter-spacing: .35em;
  font-size: 10px;
}}

.search-row {{
  margin-top: 24px;
  display: grid;
  grid-template-columns: 1fr 170px 170px 170px auto;
  gap: 14px;
  align-items: center;
}}

.search-row input,
.search-row select {{
  height: 58px;
  background: rgba(0,0,0,.44);
  border: 1px solid rgba(255,255,255,.13);
  color: white;
  padding: 0 18px;
  font-family: inherit;
  letter-spacing: .12em;
}}

.result-count {{
  color: rgba(255,255,255,.72);
  letter-spacing: .16em;
  white-space: nowrap;
}}

main {{
  padding: 0 7vw 70px;
}}

.card-grid {{
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 18px;
}}

.shop-card {{
  background: rgba(8,8,8,.78);
  border: 1px solid rgba(255,255,255,.105);
  min-height: 310px;
  padding: 24px;
  position: relative;
}}

.shop-card:hover {{
  border-color: rgba(255,255,255,.25);
}}

.card-meta {{
  display: flex;
  justify-content: space-between;
  color: rgba(255,255,255,.46);
  font-size: 12px;
  letter-spacing: .14em;
}}

.shop-card h3 {{
  margin: 26px 0 7px;
  font-size: 21px;
  font-weight: 400;
  letter-spacing: .13em;
}}

.brand-en {{
  color: rgba(255,255,255,.45);
  letter-spacing: .38em;
  font-size: 11px;
}}

.badges {{
  margin-top: 18px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}}

.badge {{
  border: 1px solid rgba(255,255,255,.14);
  padding: 5px 9px;
  font-size: 11px;
  color: rgba(255,255,255,.75);
  letter-spacing: .11em;
}}

.summary {{
  margin-top: 18px;
  min-height: 78px;
  color: rgba(255,255,255,.78);
  line-height: 1.8;
  font-size: 13px;
}}

.post-info {{
  margin-top: 18px;
  display: flex;
  align-items: baseline;
  gap: 10px;
}}

.post-num {{
  font-size: 34px;
}}

.post-label {{
  color: rgba(255,255,255,.5);
  font-size: 12px;
  letter-spacing: .15em;
}}

.detail-button,
.link-button {{
  margin-top: 18px;
  width: 100%;
  height: 48px;
  background: transparent;
  color: white;
  border: 1px solid rgba(255,255,255,.15);
  font-family: inherit;
  letter-spacing: .2em;
  cursor: pointer;
  display: grid;
  place-items: center;
  text-decoration: none;
}}

.post-details {{
  display: none;
  margin-top: 18px;
  border-top: 1px solid rgba(255,255,255,.1);
  padding-top: 16px;
}}

.post-details.open {{
  display: block;
}}

.post-item {{
  margin-top: 14px;
  padding: 14px;
  border: 1px solid rgba(255,255,255,.08);
  background: rgba(255,255,255,.025);
}}

.post-item p {{
  color: rgba(255,255,255,.76);
  font-size: 13px;
  line-height: 1.8;
}}

.post-item a {{
  color: white;
}}

.hidden {{
  display: none !important;
}}

@media (max-width: 980px) {{
  .brand-block {{
    grid-template-columns: 1fr;
    gap: 20px;
  }}

  .logo-mark {{
    font-size: 92px;
  }}

  .brand-name {{
    font-size: 30px;
    letter-spacing: .32em;
  }}

  .type-tabs {{
    display: flex;
    overflow-x: auto;
  }}

  .type-tab {{
    min-width: 165px;
  }}

  .search-row {{
    grid-template-columns: 1fr;
  }}

  .card-grid {{
    grid-template-columns: 1fr;
  }}

  .top-nav {{
    display: none;
  }}
}}

@media (max-width: 520px) {{
  .hero,
  main {{
    padding-left: 18px;
    padding-right: 18px;
  }}

  .brand-name {{
    font-size: 24px;
    letter-spacing: .22em;
  }}

  .copy {{
    font-size: 14px;
  }}
}}
</style>
</head>

<body>

<section class="hero">
  <nav class="top-nav">
    <span>ABOUT</span>
    <span>FAQ</span>
    <span>CONTACT</span>
  </nav>

  <div class="brand-block">
    <div class="logo-mark">CR</div>
    <div>
      <div class="brand-name">CARDRADAR</div>
      <div class="brand-sub">TRADING CARD PRICE RADAR</div>
      <div class="copy">すべてのカードに、<br>いまの価値を。</div>
      <div class="updated">LAST UPDATE : {updated_at}</div>
    </div>
  </div>

  <div class="find-title">何を探す？</div>

  <div class="type-tabs">
    <button class="type-tab active" data-filter-type="source" data-filter-value="all" onclick="setFilter('source','all')"><span>すべて</span><small>ALL</small></button>
"""

    for st, meta in TYPE_META.items():
        html += f"""
    <button class="type-tab" data-filter-type="source" data-filter-value="{st}" onclick="setFilter('source','{st}')"><span>{meta["label"]}</span><small>{meta["en"]}</small></button>
"""

    html += """
  </div>

  <div class="search-row">
    <input id="searchInput" type="text" placeholder="店舗名・カード名・ブランド名で検索">

    <select id="brandFilter" onchange="setFilter('brand', this.value)">
      <option value="all">ブランド</option>
"""

    for b in unique_values("brand_id", "brand"):
        html += f'<option value="{b["id"]}">{b["label"]}</option>\n'

    html += """
    </select>

    <select id="areaFilter" onchange="setFilter('area', this.value)">
      <option value="all">地域</option>
"""

    for a in unique_values("area_id", "area"):
        html += f'<option value="{a["id"]}">{a["label"]}</option>\n'

    html += """
    </select>

    <select id="typeFilter" onchange="setFilter('source', this.value)">
      <option value="all">買取タイプ</option>
"""

    for st, meta in TYPE_META.items():
        html += f'<option value="{st}">{meta["label"]}</option>\n'

    html += """
    </select>

    <div class="result-count">検索結果：<span id="resultCount">0</span>件</div>
  </div>
</section>

<main>
  <div class="card-grid">
"""

    for source, posts in all_items:
        st = source["source_type"]
        meta = TYPE_META[st]
        safe_desc = html_lib.escape(source.get("description", ""))
        safe_search = html_lib.escape(search_text(source))
        source_id = re.sub(r"[^a-zA-Z0-9_-]", "_", source["name"] + "_" + st)

        html += f"""
    <article class="shop-card"
      data-source="{st}"
      data-brand="{source["brand_id"]}"
      data-area="{source["area_id"]}"
      data-search="{safe_search}"
    >
      <div class="card-meta">
        <span>{source["area"]}</span>
        <span>{meta["label"]}</span>
      </div>

      <h3>{source["name"]}</h3>
      <div class="brand-en">{source["brand"]}</div>

      <div class="badges">
        <span class="badge">{meta["label"]}</span>
        <span class="badge">{source["area"]}</span>
        <span class="badge">{source["brand"]}</span>
      </div>

      <div class="summary">{safe_desc}</div>
"""

        if st in ["official_price_list", "market_price_link"]:
            html += f"""
      <a class="link-button" href="{source["official_url"]}" target="_blank" rel="noopener noreferrer">ページを開く →</a>
"""
        else:
            html += f"""
      <div class="post-info">
        <span class="post-num">{len(posts)}</span>
        <span class="post-label">最新投稿</span>
      </div>

      <button class="detail-button" onclick="toggleDetails('{source_id}')">詳細を見る →</button>

      <div class="post-details" id="{source_id}">
"""
            if posts:
                for post in posts:
                    safe_summary = html_lib.escape(post["summary"])
                    html += f"""
        <div class="post-item">
          <p>{safe_summary}</p>
          <a href="{post["tweet_url"]}" target="_blank" rel="noopener noreferrer">元投稿をXで開く</a>
        </div>
"""
            else:
                html += '<div class="post-item"><p>該当する投稿が見つかりませんでした。</p></div>'

            html += """
      </div>
"""

        html += """
    </article>
"""

    html += """
  </div>
</main>

<script>
const filters = {
  source: "all",
  brand: "all",
  area: "all",
  search: ""
};

function setFilter(type, value) {
  filters[type] = value;

  if (type === "source") {
    document.querySelectorAll('[data-filter-type="source"]').forEach(btn => {
      btn.classList.toggle("active", btn.dataset.filterValue === value);
    });

    const typeFilter = document.getElementById("typeFilter");
    if (typeFilter) typeFilter.value = value;
  }

  applyFilters();
}

function applyFilters() {
  filters.search = document.getElementById("searchInput").value.trim().toLowerCase();

  const cards = document.querySelectorAll(".shop-card");
  let count = 0;

  cards.forEach(card => {
    const sourceOk = filters.source === "all" || card.dataset.source === filters.source;
    const brandOk = filters.brand === "all" || card.dataset.brand === filters.brand;
    const areaOk = filters.area === "all" || card.dataset.area === filters.area;
    const searchOk = !filters.search || card.dataset.search.toLowerCase().includes(filters.search);

    if (sourceOk && brandOk && areaOk && searchOk) {
      card.classList.remove("hidden");
      count++;
    } else {
      card.classList.add("hidden");
    }
  });

  document.getElementById("resultCount").textContent = count;
}

function toggleDetails(id) {
  const el = document.getElementById(id);
  if (el) el.classList.toggle("open");
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("searchInput").addEventListener("input", applyFilters);
  applyFilters();
});
</script>

</body>
</html>
"""
    return html


def main():
    updated_at = datetime.now().strftime("%Y/%m/%d %H:%M")
    posts_by_source = {}
    all_data = []

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ],
        )

        page = browser.new_page()

        for source in SOURCES:
            source_id = source["name"] + "_" + source["source_type"]
            posts_by_source[source_id] = []

            print("")
            print("===================")
            print(source["name"])
            print("===================")

            if source["source_type"] in ["official_price_list", "market_price_link"]:
                all_data.append({
                    **source,
                    "buy_type_label": TYPE_META[source["source_type"]]["label"],
                    "collected_at": updated_at,
                })
                continue

            candidates = []
            seen = set()

            try:
                page.goto(source["url"], wait_until="domcontentloaded", timeout=60000)
                time.sleep(10)
                page.wait_for_selector("article", timeout=30000)

                for _ in range(6):
                    page.mouse.wheel(0, 1400)
                    time.sleep(3)

                tweets = page.locator("article")
                count = tweets.count()
                print("検出:", count)

                for i in range(min(count, CHECK_POSTS_PER_SOURCE)):
                    tweet = tweets.nth(i)
                    text = tweet.inner_text()
                    url = get_status_url(tweet)

                    if not url or url in seen:
                        continue

                    if not is_target_post(text, source["source_type"]):
                        continue

                    image_urls = get_image_urls(tweet)

                    if not image_urls and "買取" not in text:
                        continue

                    seen.add(url)

                    post = {
                        "source_type": source["source_type"],
                        "buy_type_label": TYPE_META[source["source_type"]]["label"],
                        "shop_name": source["name"],
                        "brand": source["brand"],
                        "brand_id": source["brand_id"],
                        "area": source["area"],
                        "area_id": source["area_id"],
                        "tweet_url": url,
                        "status_id": get_status_id(url),
                        "summary": clean_tweet_text(text),
                        "image_urls": image_urls,
                        "image_count": len(image_urls),
                        "collected_at": updated_at,
                    }

                    candidates.append(post)

                candidates.sort(key=lambda x: x["status_id"], reverse=True)
                posts = candidates[:MAX_POSTS_PER_SOURCE]
                posts_by_source[source_id] = posts
                all_data.extend(posts)

                print("採用:", len(posts))

            except Exception as e:
                print("取得エラー:", e)

        browser.close()

    html = build_html(posts_by_source, updated_at)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print("")
    print("index.html を生成しました")
    print("data.json を生成しました")
    print("データ件数:", len(all_data))

    input("Enterで終了")


if __name__ == "__main__":
    main()
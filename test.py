import importlib
import importlib.util
import time
import re
import json
import html as html_lib
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote


# =========================
# 基本設定
# =========================

USER_DATA_DIR = "userdata"
Path(USER_DATA_DIR).mkdir(exist_ok=True)

STORES_DIR = Path("stores")
STORES_DIR.mkdir(exist_ok=True)

MAX_POSTS_PER_SOURCE = 3
CHECK_POSTS_PER_SOURCE = 60


# =========================
# 買取タイプ
# =========================

TYPE_ORDER = [
    "x_post_single",
    "x_post_box",
    "x_post_fixed",
    "x_post_psa",
    "official_price_list",
    "market_price_link",
]

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
        "en": "FIXED",
        "desc": "ノーマル・RR・ARなどのまとめ買取",
    },
    "x_post_psa": {
        "label": "PSA買取",
        "en": "PSA",
        "desc": "PSA・鑑定品の買取",
    },
    "official_price_list": {
        "label": "公式Web買取表",
        "en": "OFFICIAL",
        "desc": "公式サイト掲載の買取表",
    },
    "market_price_link": {
        "label": "相場確認",
        "en": "MARKET",
        "desc": "メルカリ等の相場確認リンク",
    },
}


# =========================
# X検索URL
# =========================

def x_search_url(account, words):
    query = f"from:{account} {words} filter:images"
    return "https://x.com/search?q=" + quote(query) + "&src=typed_query&f=live"


SINGLE_WORDS = "(ポケカ OR ポケモンカード OR Pokemon) (買取 OR 高価買取 OR 買取表 OR WANTED OR 募集)"
BOX_WORDS = "(ポケカ OR ポケモンカード OR Pokemon) (BOX OR box OR 未開封 OR シュリンク OR パック OR カートン OR ボックス) (買取 OR 高価買取 OR 募集)"
FIXED_WORDS = "(ポケカ OR ポケモンカード OR Pokemon) (定額 OR 一律 OR まとめ買取 OR 最低保証 OR ノーマル OR RR OR AR OR 汎用 OR ストレージ) (買取 OR 募集)"
PSA_WORDS = "(ポケカ OR ポケモンカード OR Pokemon) (PSA OR PSA10 OR PSA9 OR 鑑定品 OR ARS OR BGS OR 鑑定) (買取 OR 高価買取 OR 募集)"


# =========================
# 店舗・情報源
# =========================

SOURCES = [
    # ドラゴンスター
    {
        "id": "ds-otachu-single",
        "source_type": "x_post_single",
        "shop_name": "ドラスタ オタロード中央",
        "shop_slug": "dragonstar-otaroad-chuo",
        "brand": "ドラゴンスター",
        "brand_id": "dragonstar",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "ドラゴンスター オタロード中央店のポケカシングル買取情報。",
        "url": x_search_url("ds_otaroad_chuo", SINGLE_WORDS),
    },
    {
        "id": "ds-honten-single",
        "source_type": "x_post_single",
        "shop_name": "ドラスタ 日本橋本店",
        "shop_slug": "dragonstar-nihonbashi-honten",
        "brand": "ドラゴンスター",
        "brand_id": "dragonstar",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "ドラゴンスター 日本橋本店のポケカシングル買取情報。",
        "url": x_search_url("ds_nipponbashi", SINGLE_WORDS),
    },
    {
        "id": "ds-dora2-single",
        "source_type": "x_post_single",
        "shop_name": "ドラスタ 日本橋2号店",
        "shop_slug": "dragonstar-nihonbashi-2",
        "brand": "ドラゴンスター",
        "brand_id": "dragonstar",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "ドラゴンスター 日本橋2号店のポケカ買取表・WANTED情報。",
        "url": x_search_url("ds_nipponbashi2", SINGLE_WORDS),
    },
    {
        "id": "ds-dora3-single",
        "source_type": "x_post_single",
        "shop_name": "ドラスタ 日本橋3号店",
        "shop_slug": "dragonstar-nihonbashi-3",
        "brand": "ドラゴンスター",
        "brand_id": "dragonstar",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "ドラゴンスター 日本橋3号店のポケカシングル買取情報。",
        "url": x_search_url("ds_nipponbashi3", SINGLE_WORDS),
    },
    {
        "id": "ds-nansan-single",
        "source_type": "x_post_single",
        "shop_name": "ドラスタ なんさん通り店",
        "shop_slug": "dragonstar-nansan",
        "brand": "ドラゴンスター",
        "brand_id": "dragonstar",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "ドラゴンスター なんさん通り店のポケカ買取情報。",
        "url": x_search_url("ds_namba_nansan", SINGLE_WORDS),
    },

    # 晴れる屋2
    {
        "id": "hareruya2-namba-single",
        "source_type": "x_post_single",
        "shop_name": "晴れる屋2なんば",
        "shop_slug": "hareruya2-namba",
        "brand": "晴れる屋2",
        "brand_id": "hareruya2",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "晴れる屋2なんば店のポケカ買取表。",
        "url": x_search_url("hareruya2namba", SINGLE_WORDS),
    },

    # カードラボ
    {
        "id": "cardlabo-namba-single",
        "source_type": "x_post_single",
        "shop_name": "カードラボなんば店",
        "shop_slug": "cardlabo-namba",
        "brand": "カードラボ",
        "brand_id": "cardlabo",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "カードラボなんば店のポケカ買取情報。",
        "url": x_search_url("namba_clabo", SINGLE_WORDS),
    },
    {
        "id": "cardlabo-nihonbashi-single",
        "source_type": "x_post_single",
        "shop_name": "カードラボ大阪日本橋店",
        "shop_slug": "cardlabo-osaka-nihonbashi",
        "brand": "カードラボ",
        "brand_id": "cardlabo",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "カードラボ大阪日本橋店のポケカ買取情報。",
        "url": x_search_url("nipponbashi_lab", SINGLE_WORDS),
    },

    # GIRAFULL
    {
        "id": "girafull-namba-single",
        "source_type": "x_post_single",
        "shop_name": "GIRAFULLなんば店",
        "shop_slug": "girafull-namba",
        "brand": "GIRAFULL",
        "brand_id": "girafull",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "GIRAFULLなんば店のポケカ買取情報。",
        "url": x_search_url("GIRAFULL_Namba", SINGLE_WORDS),
    },
    {
        "id": "girafull-nihonbashi-single",
        "source_type": "x_post_single",
        "shop_name": "GIRAFULL大阪日本橋店",
        "shop_slug": "girafull-osaka-nihonbashi",
        "brand": "GIRAFULL",
        "brand_id": "girafull",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "GIRAFULL大阪日本橋店のポケカ買取情報。",
        "url": x_search_url("girafull_o_n", SINGLE_WORDS),
    },
    {
        "id": "girafull-otaroad-single",
        "source_type": "x_post_single",
        "shop_name": "GIRAFULLオタロード店",
        "shop_slug": "girafull-otaroad",
        "brand": "GIRAFULL",
        "brand_id": "girafull",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "GIRAFULLオタロード店のポケカ買取情報。",
        "url": x_search_url("GIRAFULLOTARODO", SINGLE_WORDS),
    },

    # アムタフ
    {
        "id": "amtaf-single",
        "source_type": "x_post_single",
        "shop_name": "アムタフ",
        "shop_slug": "amtaf",
        "brand": "アムタフ",
        "brand_id": "amtaf",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "アムタフのポケカシングル買取情報。",
        "url": x_search_url("AMTAF_SHOP", SINGLE_WORDS),
    },
    {
        "id": "amtaf-box",
        "source_type": "x_post_box",
        "shop_name": "アムタフ",
        "shop_slug": "amtaf",
        "brand": "アムタフ",
        "brand_id": "amtaf",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "アムタフのポケカ未開封BOX・パック買取情報。",
        "url": x_search_url("AMTAF_SHOP", BOX_WORDS),
    },
    {
        "id": "amtaf-fixed",
        "source_type": "x_post_fixed",
        "shop_name": "アムタフ",
        "shop_slug": "amtaf",
        "brand": "アムタフ",
        "brand_id": "amtaf",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "アムタフの定額買取・まとめ買取情報。",
        "url": x_search_url("AMTAF_SHOP", FIXED_WORDS),
    },

    # GOTCHA
    {
        "id": "gotcha-single",
        "source_type": "x_post_single",
        "shop_name": "GOTCHA!",
        "shop_slug": "gotcha",
        "brand": "GOTCHA!",
        "brand_id": "gotcha",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "GOTCHA!のポケカシングル買取情報。",
        "url": x_search_url("cardshop_gotcha", SINGLE_WORDS),
    },
    {
        "id": "gotcha-box",
        "source_type": "x_post_box",
        "shop_name": "GOTCHA!",
        "shop_slug": "gotcha",
        "brand": "GOTCHA!",
        "brand_id": "gotcha",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "GOTCHA!のポケカ未開封BOX・パック買取情報。",
        "url": x_search_url("cardshop_gotcha", BOX_WORDS),
    },

    # KURO
    {
        "id": "kuro-single",
        "source_type": "x_post_single",
        "shop_name": "KURO",
        "shop_slug": "kuro",
        "brand": "KURO",
        "brand_id": "kuro",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "KUROのポケカシングル買取情報。",
        "url": x_search_url("kuro_tcg", SINGLE_WORDS),
    },
    {
        "id": "kuro-box",
        "source_type": "x_post_box",
        "shop_name": "KURO",
        "shop_slug": "kuro",
        "brand": "KURO",
        "brand_id": "kuro",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "KUROのポケカ未開封BOX・パック・カートン買取情報。",
        "url": x_search_url("kuro_tcg", BOX_WORDS),
    },

    # 買取ミミ
    {
        "id": "mimi-single",
        "source_type": "x_post_single",
        "shop_name": "買取ミミ",
        "shop_slug": "kaitori-mimi",
        "brand": "買取ミミ",
        "brand_id": "mimi",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "買取ミミのポケカシングル買取情報。",
        "url": x_search_url("mimi_kaitori", SINGLE_WORDS),
    },
    {
        "id": "mimi-fixed",
        "source_type": "x_post_fixed",
        "shop_name": "買取ミミ",
        "shop_slug": "kaitori-mimi",
        "brand": "買取ミミ",
        "brand_id": "mimi",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "買取ミミの定額買取・まとめ買取情報。",
        "url": x_search_url("mimi_kaitori", FIXED_WORDS),
    },

    # 公式Web買取表
    {
        "id": "clove-official",
        "source_type": "official_price_list",
        "shop_name": "Clove Base",
        "shop_slug": "clove-base",
        "brand": "Clove",
        "brand_id": "clove",
        "area": "公式Web",
        "area_id": "official-web",
        "description": "ポケモンカードの公式Web買取表。",
        "official_url": "https://base.clove.jp/prices/pokemon",
    },
    {
        "id": "fullahead-official",
        "source_type": "official_price_list",
        "shop_name": "フルアヘッド",
        "shop_slug": "fullahead",
        "brand": "フルアヘッド",
        "brand_id": "fullahead",
        "area": "公式Web",
        "area_id": "official-web",
        "description": "ポケカを含むTCGの公式Web買取表。",
        "official_url": "https://fullahead-buy.com/",
    },

    # 相場確認
    {
        "id": "mercari-pokemon",
        "source_type": "market_price_link",
        "shop_name": "メルカリ ポケカ相場",
        "shop_slug": "mercari-pokemon",
        "brand": "メルカリ",
        "brand_id": "mercari",
        "area": "相場確認",
        "area_id": "market",
        "description": "メルカリでポケカ相場を確認する検索リンク。",
        "official_url": "https://jp.mercari.com/search?keyword=%E3%83%9D%E3%82%B1%E3%82%AB",
    },
    {
        "id": "mercari-box",
        "source_type": "market_price_link",
        "shop_name": "メルカリ BOX相場",
        "shop_slug": "mercari-box",
        "brand": "メルカリ",
        "brand_id": "mercari",
        "area": "相場確認",
        "area_id": "market",
        "description": "メルカリでポケカ未開封BOX相場を確認する検索リンク。",
        "official_url": "https://jp.mercari.com/search?keyword=%E3%83%9D%E3%82%B1%E3%82%AB%20BOX%20%E6%9C%AA%E9%96%8B%E5%B0%81",
    },
]


# =========================
# 共通関数
# =========================

def h(value):
    return html_lib.escape(str(value or ""))


def is_x_source(source):
    return source["source_type"].startswith("x_post_")


def get_source(source_id):
    for source in SOURCES:
        if source["id"] == source_id:
            return source
    return None


def get_sources_by_shop(shop_slug):
    return [s for s in SOURCES if s["shop_slug"] == shop_slug]


def get_physical_shops(area_id):
    shops = {}
    for source in SOURCES:
        if source["area_id"] != area_id:
            continue
        if source["source_type"] in ["official_price_list", "market_price_link"]:
            continue

        slug = source["shop_slug"]
        if slug not in shops:
            shops[slug] = {
                "shop_slug": slug,
                "shop_name": source["shop_name"],
                "brand": source["brand"],
                "brand_id": source["brand_id"],
                "area": source["area"],
                "area_id": source["area_id"],
                "sources": [],
            }

        shops[slug]["sources"].append(source)

    return list(shops.values())


def get_support_sources():
    return [
        s for s in SOURCES
        if s["source_type"] in ["official_price_list", "market_price_link"]
    ]


def get_unique_brands(area_id):
    brands = []
    seen = set()

    for source in SOURCES:
        if source["area_id"] != area_id:
            continue

        if source["brand_id"] in seen:
            continue

        seen.add(source["brand_id"])
        brands.append({
            "id": source["brand_id"],
            "label": source["brand"],
        })

    return brands


def get_shop_types(sources):
    types = []
    for source in sources:
        if source["source_type"] not in types:
            types.append(source["source_type"])
    return types


def get_type_labels(types):
    return [TYPE_META[t]["label"] for t in types if t in TYPE_META]


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

        if "pbs.twimg.com/media" not in src:
            continue

        src = src.replace("name=small", "name=large")
        src = src.replace("name=medium", "name=large")

        if src not in urls:
            urls.append(src)

    return urls


def clean_tweet_text(text):
    lines = []

    skip_words = [
        "さらに表示",
        "返信先:",
    ]

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        if line.startswith("@"):
            continue

        if line == "·":
            continue

        if any(word in line for word in skip_words):
            continue

        lines.append(line)

    summary = " ".join(lines)

    if len(summary) > 240:
        summary = summary[:240] + "..."

    return summary


def is_target_post(text, source_type):
    pokemon_words = [
        "ポケカ",
        "ポケモンカード",
        "ポケモンカードゲーム",
        "Pokemon",
        "pokemon",
    ]

    buy_words = [
        "買取",
        "高価買取",
        "買取表",
        "WANTED",
        "募集",
        "取扱強化",
        "買取情報",
    ]

    ng_words = [
        "大会",
        "優勝",
        "抽選",
        "販売開始",
        "BOX争奪戦",
        "争奪戦",
        "ワンピース",
        "遊戯王",
        "デュエマ",
        "MTG",
        "ヴァイス",
        "バトスピ",
        "デジカ",
        "ガンダム",
    ]

    if any(word in text for word in ng_words):
        return False

    if not any(word in text for word in pokemon_words):
        return False

    if not any(word in text for word in buy_words):
        return False

    if source_type == "x_post_box":
        box_words = [
            "BOX",
            "box",
            "未開封",
            "シュリンク",
            "パック",
            "カートン",
            "ボックス",
            "1BOX",
        ]

        box_ng_words = [
            "BOX買取以外",
            "BOX以外",
            "ボックス以外",
            "未開封BOX以外",
            "BOX対象外",
            "BOXは対象外",
        ]

        single_words = [
            "SAR",
            "SR",
            "UR",
            "HR",
            "CSR",
            "CHR",
            "AR",
            "SA",
            "ex",
            "EX",
        ]

        if not any(word in text for word in box_words):
            return False

        if any(word in text for word in box_ng_words):
            return False

        if sum(1 for word in single_words if word in text) >= 4:
            return False

        return True

    if source_type == "x_post_fixed":
        fixed_words = [
            "定額",
            "一律",
            "まとめ買取",
            "最低保証",
            "保証買取",
            "ノーマル",
            "RR",
            "AR",
            "ストレージ",
            "大量",
        ]

        return any(word in text for word in fixed_words)

    if source_type == "x_post_psa":
        psa_words = [
            "PSA",
            "PSA10",
            "PSA9",
            "鑑定品",
            "鑑定",
            "ARS",
            "BGS",
        ]

        return any(word in text for word in psa_words)

    return True


def get_posts_for_shop(posts_by_source, shop_slug):
    posts = []

    for source in get_sources_by_shop(shop_slug):
        posts.extend(posts_by_source.get(source["id"], []))

    posts.sort(key=lambda p: p.get("status_id", 0), reverse=True)
    return posts


def get_latest_post(posts):
    if not posts:
        return None

    return sorted(posts, key=lambda p: p.get("status_id", 0), reverse=True)[0]


def first_image(posts):
    for post in posts:
        for image_url in post.get("image_urls", []):
            return image_url
    return None


def json_for_script(data):
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


# =========================
# CSS
# =========================

COMMON_CSS = """
* {
  box-sizing: border-box;
}

html {
  scroll-behavior: smooth;
}

body {
  margin: 0;
  background: #050505;
  color: #f5f5f5;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, "Noto Sans JP", sans-serif;
}

body::before {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  background:
    radial-gradient(circle at 15% 13%, rgba(255,255,255,.13), transparent 17%),
    radial-gradient(circle at 22% 25%, rgba(255,255,255,.045), transparent 23%),
    linear-gradient(90deg, rgba(255,255,255,.025), transparent 35%),
    repeating-linear-gradient(0deg, rgba(255,255,255,.012), rgba(255,255,255,.012) 1px, transparent 1px, transparent 5px);
  opacity: .8;
  z-index: -2;
}

body::after {
  content: "";
  position: fixed;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(90deg, transparent 0%, transparent 70%, rgba(255,255,255,.027) 73%, transparent 77%),
    linear-gradient(90deg, transparent 0%, transparent 80%, rgba(255,255,255,.02) 82%, transparent 86%),
    linear-gradient(180deg, #080808 0%, #030303 100%);
  opacity: .95;
  z-index: -3;
}

a {
  color: inherit;
}

.page-shell {
  min-height: 100vh;
}

.hero {
  padding: 36px 7vw 30px;
}

.area-hero {
  padding-top: 18px;
  padding-bottom: 12px;
}

.area-hero .logo-mark {
  font-size: 44px;
}

.area-hero .logo-text {
  font-size: 20px;
}

.area-hero .breadcrumb {
  margin-top: 12px;
}

.area-hero .area-title {
  margin-top: 12px;
  font-size: clamp(28px, 6vw, 44px);
}

.area-hero .area-description {
  margin: 10px 0 0;
  line-height: 1.65;
}

.logo-row {
  display: flex;
  align-items: center;
  gap: 16px;
}

.logo-mark {
  font-family: "Times New Roman", serif;
  font-size: 58px;
  letter-spacing: -.16em;
  line-height: .85;
  text-shadow: 0 0 24px rgba(255,255,255,.18);
}

.logo-text {
  font-family: "Times New Roman", serif;
  letter-spacing: .36em;
  font-size: 24px;
  font-weight: 400;
}

.logo-sub {
  margin-top: 5px;
  color: rgba(255,255,255,.48);
  letter-spacing: .28em;
  font-size: 11px;
}

.hero-large {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 36px 7vw;
}

.hero-title {
  margin-top: 42px;
  font-family: "Times New Roman", serif;
  font-weight: 400;
  font-size: clamp(36px, 9vw, 76px);
  letter-spacing: .18em;
  line-height: 1.1;
}

.hero-copy {
  margin-top: 24px;
  color: rgba(255,255,255,.78);
  line-height: 2;
  letter-spacing: .1em;
}

.selector-grid {
  margin-top: 44px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}

.select-card {
  display: block;
  text-decoration: none;
  background: rgba(8,8,8,.76);
  border: 1px solid rgba(255,255,255,.12);
  padding: 28px;
  min-height: 160px;
  transition: border-color .15s ease, transform .15s ease;
}

.select-card:hover {
  border-color: rgba(255,255,255,.32);
  transform: translateY(-2px);
}

.select-card small {
  display: block;
  color: rgba(255,255,255,.45);
  letter-spacing: .28em;
  font-size: 11px;
}

.select-card strong {
  display: block;
  margin-top: 18px;
  font-size: 24px;
  letter-spacing: .12em;
  font-weight: 500;
}

.select-card p {
  margin: 16px 0 0;
  color: rgba(255,255,255,.62);
  font-size: 13px;
  line-height: 1.7;
}

.breadcrumb {
  margin-top: 24px;
  color: rgba(255,255,255,.5);
  font-size: 12px;
  letter-spacing: .12em;
}

.breadcrumb a {
  color: rgba(255,255,255,.7);
  text-decoration: none;
}

.area-title {
  margin-top: 32px;
  font-family: "Times New Roman", serif;
  font-size: clamp(34px, 9vw, 62px);
  letter-spacing: .18em;
  font-weight: 400;
}

.area-description {
  max-width: 720px;
  color: rgba(255,255,255,.72);
  line-height: 1.9;
  letter-spacing: .08em;
}

.sticky-search {
  position: sticky;
  top: 0;
  z-index: 20;
  background: rgba(5,5,5,.92);
  backdrop-filter: blur(18px);
  border-top: 1px solid rgba(255,255,255,.08);
  border-bottom: 1px solid rgba(255,255,255,.10);
  padding: 14px 7vw;
}


.compact-search {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 50;
  display: none;
  background: rgba(5,5,5,.96);
  border-bottom: 1px solid rgba(255,255,255,.1);
  padding: 8px 7vw;
  padding-top: calc(8px + env(safe-area-inset-top));
}

.compact-search input {
  width: 100%;
  height: 40px;
  background: rgba(255,255,255,.06);
  border: 1px solid rgba(255,255,255,.2);
  color: #fff;
  padding: 0 10px;
  font-size: 16px;
}

.compact-search.visible {
  display: block;
}

.menu-toggle {
  border: 1px solid rgba(255,255,255,.18);
  background: rgba(255,255,255,.05);
  color: #fff;
  padding: 10px 14px;
  cursor: pointer;
}

.menu-panel {
  display: none;
  margin-top: 10px;
  border: 1px solid rgba(255,255,255,.14);
  background: rgba(8,8,8,.95);
}

.menu-panel.open {
  display: block;
}

.menu-panel a {
  display: block;
  padding: 14px 16px;
  line-height: 1.5;
  text-decoration: none;
  border-top: 1px solid rgba(255,255,255,.08);
}

.menu-panel a:first-child {
  border-top: 0;
}

.search-main {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 12px;
  align-items: center;
}

.search-main input {
  width: 100%;
  height: 48px;
  background: rgba(255,255,255,.055);
  border: 1px solid rgba(255,255,255,.15);
  color: white;
  padding: 0 14px;
  font-size: 15px;
  outline: none;
}


.filter-toggle {
  height: 48px;
  border: 1px solid rgba(255,255,255,.16);
  background: rgba(255,255,255,.06);
  color: white;
  padding: 0 16px;
  cursor: pointer;
  white-space: nowrap;
}

.filter-panel {
  display: none;
}

.filter-panel.open {
  display: block;
}

.reset-button {
  height: 48px;
  border: 1px solid rgba(255,255,255,.16);
  background: transparent;
  color: white;
  padding: 0 16px;
  cursor: pointer;
}

.chip-row {
  margin-top: 12px;
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.filter-chip {
  flex: 0 0 auto;
  margin-right: 8px;
  margin-bottom: 6px;
  border: 1px solid rgba(255,255,255,.14);
  background: rgba(255,255,255,.04);
  color: rgba(255,255,255,.82);
  padding: 9px 12px;
  border-radius: 999px;
  cursor: pointer;
  font-size: 13px;
  white-space: nowrap;
}

.filter-chip.active {
  background: rgba(255,255,255,.18);
  border-color: rgba(255,255,255,.36);
}

.result-line {
  margin-top: 10px;
  color: rgba(255,255,255,.52);
  font-size: 12px;
  letter-spacing: .12em;
}

main {
  padding: 28px 7vw 80px;
}

.section-head {
  margin: 34px 0 18px;
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 16px;
}

.section-head h2 {
  margin: 0;
  font-family: "Times New Roman", serif;
  font-weight: 400;
  letter-spacing: .16em;
}

.section-head p {
  margin: 0;
  color: rgba(255,255,255,.48);
  font-size: 13px;
}

.shop-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}

.support-quick {
  margin-bottom: 28px;
}

.empty-tl-notice {
  margin-bottom: 28px;
  padding: 18px;
  background: rgba(255,255,255,.045);
  border: 1px solid rgba(255,255,255,.11);
}

.empty-tl-notice p {
  margin: 0;
  color: rgba(255,255,255,.72);
  line-height: 1.8;
}

.store-list {
  display: grid;
  gap: 10px;
}

.store-row {
  min-height: 0;
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 12px;
  align-items: center;
  padding: 16px;
}

.store-row.waiting {
  opacity: .72;
}

.store-row .shop-body {
  padding: 0;
}

.store-row .shop-body h3 {
  margin: 8px 0 6px;
  font-size: 18px;
}

.store-row .card-footer {
  border-top: 0;
  padding: 0;
  white-space: nowrap;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  border: 1px solid rgba(255,255,255,.14);
  color: rgba(255,255,255,.62);
  padding: 4px 8px;
  font-size: 12px;
  white-space: nowrap;
}

.shop-card {
  display: flex;
  flex-direction: column;
  background: rgba(8,8,8,.8);
  border: 1px solid rgba(255,255,255,.105);
  min-height: 460px;
  text-decoration: none;
  transition: border-color .15s ease, transform .15s ease;
  overflow: hidden;
}

.shop-card:hover {
  border-color: rgba(255,255,255,.3);
  transform: translateY(-2px);
}

.thumb-wrap {
  width: 100%;
  aspect-ratio: 4 / 3;
  background: rgba(255,255,255,.045);
  overflow: hidden;
}

.thumb-wrap img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.no-thumb {
  width: 100%;
  height: 100%;
  display: grid;
  place-items: center;
  color: rgba(255,255,255,.32);
  letter-spacing: .2em;
  font-size: 12px;
}

.shop-body {
  padding: 18px;
  flex: 1;
}

.card-meta {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: rgba(255,255,255,.48);
  font-size: 12px;
}

.shop-body h3 {
  margin: 22px 0 8px;
  font-size: 21px;
  font-weight: 600;
  letter-spacing: .06em;
}

.shop-brand {
  color: rgba(255,255,255,.52);
  font-size: 12px;
  letter-spacing: .2em;
}

.badges {
  margin-top: 16px;
  display: flex;
  gap: 7px;
  flex-wrap: wrap;
}

.badge {
  border: 1px solid rgba(255,255,255,.14);
  padding: 5px 8px;
  font-size: 11px;
  color: rgba(255,255,255,.72);
}

.summary {
  margin-top: 16px;
  color: rgba(255,255,255,.72);
  line-height: 1.75;
  font-size: 13px;
}

.card-footer {
  padding: 0 18px 18px;
  color: rgba(255,255,255,.82);
  letter-spacing: .12em;
  font-size: 13px;
}

.ad-card {
  background:
    linear-gradient(135deg, rgba(255,255,255,.075), rgba(255,255,255,.02));
  border: 1px solid rgba(255,255,255,.14);
  padding: 22px;
  min-height: 190px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.ad-card small {
  color: rgba(255,255,255,.42);
  letter-spacing: .25em;
  font-size: 11px;
}

.ad-card strong {
  margin-top: 12px;
  font-size: 20px;
  letter-spacing: .08em;
}

.ad-card p {
  color: rgba(255,255,255,.62);
  line-height: 1.7;
  font-size: 13px;
}

.store-layout {
  max-width: 1240px;
  margin: 0 auto;
}

.store-header {
  margin-bottom: 24px;
}

.store-title {
  font-size: clamp(34px, 8vw, 60px);
  letter-spacing: .1em;
  font-weight: 500;
  margin: 30px 0 10px;
}

.store-sub {
  color: rgba(255,255,255,.58);
  letter-spacing: .16em;
}

.image-section {
  margin-top: 34px;
}

.image-section h2 {
  font-family: "Times New Roman", serif;
  font-weight: 400;
  letter-spacing: .16em;
}

.image-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 22px;
}

.image-card {
  background: rgba(8,8,8,.84);
  border: 1px solid rgba(255,255,255,.11);
  overflow: hidden;
  cursor: pointer;
}

.image-card img {
  width: 100%;
  display: block;
}

.image-info {
  padding: 14px;
}

.image-info p {
  margin: 0;
  color: rgba(255,255,255,.7);
  line-height: 1.7;
  font-size: 13px;
}

.image-info small {
  display: block;
  margin-top: 10px;
  color: rgba(255,255,255,.42);
}

.link-card {
  background: rgba(8,8,8,.82);
  border: 1px solid rgba(255,255,255,.11);
  padding: 22px;
}

.link-card a {
  display: inline-block;
  margin-top: 16px;
  text-decoration: none;
  border: 1px solid rgba(255,255,255,.18);
  padding: 12px 16px;
}

.modal {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.84);
  z-index: 100;
  display: none;
  padding: 20px;
  overflow-y: auto;
}

.modal.open {
  display: block;
}

.modal-inner {
  max-width: 920px;
  margin: 0 auto;
  background: #090909;
  border: 1px solid rgba(255,255,255,.16);
  padding: 16px;
}

.modal-close {
  display: block;
  margin-left: auto;
  background: transparent;
  border: 1px solid rgba(255,255,255,.18);
  color: white;
  padding: 10px 13px;
  cursor: pointer;
}

.modal-image {
  width: 100%;
  display: block;
  margin-top: 14px;
}

.modal-summary {
  color: rgba(255,255,255,.78);
  line-height: 1.8;
  margin-top: 14px;
}

.modal-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 14px;
}

.modal-actions a,
.modal-actions button {
  background: transparent;
  color: white;
  border: 1px solid rgba(255,255,255,.18);
  padding: 11px 13px;
  text-decoration: none;
  cursor: pointer;
}

.tweet-embed {
  margin-top: 18px;
}

.hidden {
  display: none !important;
}

@media (max-width: 1100px) {
  .shop-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .hero {
    padding: 20px 12px 16px;
  }

  .area-hero {
    padding-top: 14px;
    padding-bottom: 10px;
  }

  .hero-large {
    padding: 20px 12px;
  }

  .sticky-search {
    padding: 10px 12px;
  }

  .compact-search {
    padding-left: 12px;
    padding-right: 12px;
  }

  .chip-row {
    gap: 6px;
  }

  .filter-chip {
    padding: 8px 10px;
    font-size: 12px;
  }

  .store-row {
    grid-template-columns: 1fr;
  }

  .store-row .card-footer {
    margin-top: 4px;
  }

  .selector-grid,
  .shop-grid,
  .image-grid {
    grid-template-columns: 1fr;
  }

  .search-main {
    grid-template-columns: 1fr 1fr;
  }

  .search-main input {
    grid-column: 1 / -1;
  }

  .filter-toggle,
  .reset-button {
    width: 100%;
  }

  main {
    padding: 20px 12px 72px;
  }

  .section-head {
    display: block;
  }

  .shop-card {
    min-height: auto;
  }

  .thumb-wrap {
    aspect-ratio: 16 / 10;
  }

  .image-grid {
    gap: 26px;
  }
}
"""


def html_shell(title, content, base_prefix=""):
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{h(title)}</title>
<meta name="description" content="CardRadarは、ポケカのシングル買取・BOX買取・定額買取・PSA買取・公式Web買取表・相場確認を探せるサイトです。">
<link rel="icon" type="image/png" href="{base_prefix}icon-512.png">
<link rel="apple-touch-icon" href="{base_prefix}icon-512.png">
<meta name="theme-color" content="#050505">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<style>
{COMMON_CSS}
</style>
</head>
<body>
{content}
</body>
</html>
"""


def logo_html(base_prefix=""):
    return f"""
<div class="logo-row">
  <div class="logo-mark">CR</div>
  <div>
    <div class="logo-text">CARDRADAR</div>
    <div class="logo-sub">TRADING CARD PRICE RADAR</div>
  </div>
</div>
"""


# =========================
# ページ生成：トップ
# =========================

def build_index_page(updated_at):
    content = f"""
<div class="page-shell">
  <section class="hero-large">
    {logo_html()}

    <div class="hero-title">AREA<br>SELECT</div>

    <p class="hero-copy">
      ポケカ買取情報を、地域・店舗・買取タイプ別に。<br>
      X買取表、BOX買取、定額買取、PSA買取、公式Web買取表、相場確認まで。
    </p>

    <div class="selector-grid">
      <a class="select-card" href="osaka.html">
        <small>KANSAI</small>
        <strong>大阪</strong>
        <p>日本橋エリアのポケカ買取表・BOX買取・定額買取を確認。</p>
      </a>

      <a class="select-card" href="#">
        <small>KANTO</small>
        <strong>東京</strong>
        <p>秋葉原など、今後追加予定。</p>
      </a>

      <a class="select-card" href="#">
        <small>CHUBU</small>
        <strong>愛知</strong>
        <p>大須など、今後追加予定。</p>
      </a>
    </div>

    <div class="updated">LAST UPDATE : {h(updated_at)}</div>
  </section>
</div>
"""
    return html_shell("CardRadar｜ポケカ買取情報を探す", content)


# =========================
# ページ生成：大阪
# =========================

def build_osaka_page(updated_at):
    content = f"""
<div class="page-shell">
  <section class="hero-large">
    {logo_html()}

    <div class="breadcrumb">
      <a href="index.html">TOP</a> / OSAKA
    </div>

    <div class="hero-title">OSAKA</div>

    <p class="hero-copy">
      大阪エリアのカードショップ買取情報。<br>
      まずは日本橋エリアから対応中です。
    </p>

    <div class="selector-grid">
      <a class="select-card" href="osaka-nihonbashi.html">
        <small>OSAKA</small>
        <strong>日本橋</strong>
        <p>ポケカ買取表、BOX買取、定額買取、公式Web買取表、相場確認。</p>
      </a>

      <a class="select-card" href="#">
        <small>COMING SOON</small>
        <strong>梅田</strong>
        <p>今後追加予定。</p>
      </a>

      <a class="select-card" href="#">
        <small>COMING SOON</small>
        <strong>天王寺</strong>
        <p>今後追加予定。</p>
      </a>
    </div>

    <div class="updated">LAST UPDATE : {h(updated_at)}</div>
  </section>
</div>
"""
    return html_shell("CardRadar｜大阪エリア", content)


# =========================
# ページ生成：日本橋
# =========================

def build_area_page(posts_by_source, updated_at):
    shops = get_physical_shops("osaka-nihonbashi")
    support_sources = get_support_sources()
    brands = get_unique_brands("osaka-nihonbashi")

    cards_html = ""
    timeline_items = []

    for shop in shops:
        posts = get_posts_for_shop(posts_by_source, shop["shop_slug"])
        latest = get_latest_post(posts)
        types = get_shop_types(shop["sources"])
        type_labels = get_type_labels(types)

        latest_count = len(posts)
        latest_status = f"最新{latest_count}件" if latest_count else "取得待ち"
        waiting_class = " waiting" if latest_count == 0 else ""
        latest_summary = latest["summary"] if latest else "投稿取得待ちです。公式Web買取表・相場確認もあわせて確認してください。"

        badges = "".join([f'<span class="badge">{h(label)}</span>' for label in type_labels])

        cards_html += f"""
<a class="shop-card store-row{waiting_class}"
   href="stores/{h(shop["shop_slug"])}.html"
   data-types="{' '.join(types)}"
   data-brand="{h(shop["brand_id"])}"
   data-search="{h(shop["shop_name"] + ' ' + shop["brand"] + ' ' + ' '.join(type_labels) + ' ' + latest_summary)}"
>
  <div class="shop-body">
    <div class="card-meta"><span>{h(shop["area"])}</span><span class="status-pill">{h(latest_status)}</span></div>
    <h3>{h(shop["shop_name"])}</h3>
    <div class="shop-brand">{h(shop["brand"])}</div>
    <div class="badges">{badges}</div>
    <div class="summary">{h(latest_summary)}</div>
  </div>
  <div class="card-footer">店舗ページ →</div>
</a>
"""

        for source in shop["sources"]:
            if not is_x_source(source):
                continue
            meta = TYPE_META[source["source_type"]]
            for post in posts_by_source.get(source["id"], []):
                timeline_items.append({
                    "status_id": post.get("status_id", 0),
                    "brand_id": shop["brand_id"],
                    "shop_name": shop["shop_name"],
                    "shop_slug": shop["shop_slug"],
                    "type_key": source["source_type"],
                    "type_label": meta["label"],
                    "updated_info": post.get("date_text", ""),
                    "summary": post.get("summary", ""),
                    "tweet_url": post.get("tweet_url", ""),
                    "image_url": post.get("image_urls", [None])[0] if post.get("image_urls") else None,
                    "search": f'{shop["shop_name"]} {meta["label"]} {post.get("summary", "")}',
                })

    support_html = ""
    for source in support_sources:
        meta = TYPE_META[source["source_type"]]
        support_html += f"""
<div class="link-card">
  <div class="card-meta"><span>{h(source["area"])}</span><span>{h(meta["label"])}</span></div>
  <h3>{h(source["shop_name"])}</h3>
  <p class="summary">{h(source["description"])}</p>
  <a href="{h(source["official_url"])}" target="_blank" rel="noopener noreferrer">ページを開く →</a>
</div>
"""

    if timeline_items:
        timeline_section = """
    <section id="timelineSection">
      <div class="section-head"><h2>BUYBACK TL</h2><p>投稿タイムライン</p></div>
      <div class="shop-grid" id="timelineGrid"></div>
    </section>
"""
    else:
        timeline_section = """
    <div class="empty-tl-notice" id="timelineEmptyNotice">
      <p>現在取得できている投稿はありません。<a href="#supportQuick">公式Web買取表・相場確認はこちら</a>から確認できます。</p>
    </div>
    <div id="timelineGrid" class="hidden"></div>
"""

    type_buttons = "<button class=\"filter-chip active\" onclick=\"toggleType('all', this)\">すべて</button>"
    for type_key in TYPE_ORDER:
        meta = TYPE_META[type_key]
        type_buttons += f"<button class=\"filter-chip\" onclick=\"toggleType('{h(type_key)}', this)\">{h(meta['label'])}</button>"

    brand_buttons = "".join([f"<button class=\"filter-chip\" onclick=\"toggleBrand('{h(b['id'])}', this)\">{h(b['label'])}</button>" for b in brands])

    content = f"""
<div class="page-shell">
  <section class="hero area-hero" id="heroArea">{logo_html()}
    <div style="margin-top:10px;"><button class="menu-toggle" onclick="toggleMenu()">☰ メニュー</button><div class="menu-panel" id="menuPanel"><a href="index.html">トップ</a><a href="osaka-nihonbashi.html">大阪・日本橋</a><a href="#shopGrid">店舗一覧</a><a href="#supportLinks">公式Web買取表</a><a href="#supportLinks">相場確認</a><a href="#">掲載について</a></div></div>
    <div class="breadcrumb"><a href="index.html">TOP</a> / <a href="osaka.html">OSAKA</a> / NIHONBASHI</div>
    <h1 class="area-title">NIHONBASHI</h1>
    <p class="area-description">大阪・日本橋エリアのポケカ買取TLを、買取タイプ別に確認できます。</p>
    <div class="updated">LAST UPDATE : {h(updated_at)}</div>
  </section>

  <div id="compactSearch" class="compact-search"><input id="compactSearchInput" type="text" placeholder="検索"></div>

  <div class="sticky-search">
    <div class="search-main">
      <input id="searchInput" type="text" placeholder="店舗名・買取タイプ・概要で検索">
      <button class="filter-toggle" onclick="toggleFilterPanel()">絞り込み</button>
      <button class="reset-button" onclick="resetFilters()">リセット</button>
    </div>
    <div class="result-line">表示中：<span id="resultCount">0</span>件 / <span id="filterSummary">すべて・新着順</span></div>
    <div class="filter-panel" id="filterPanel">
      <div class="chip-row" id="typeRow">{type_buttons}</div>
      <div class="chip-row" id="brandRow">{brand_buttons}</div>
      <div class="chip-row" id="sortRow">
        <button class="filter-chip active" onclick="setSort('latest', this)">新着順</button>
        <button class="filter-chip" onclick="setSort('x_post_box', this)">BOX優先</button>
        <button class="filter-chip" onclick="setSort('x_post_fixed', this)">定額優先</button>
        <button class="filter-chip" onclick="setSort('x_post_psa', this)">PSA優先</button>
        <button class="filter-chip" onclick="setSort('x_post_single', this)">シングル優先</button>
        <button class="filter-chip" onclick="setSort('shop_name', this)">店舗名順</button>
      </div>
    </div>
  </div>

  <main>
    <section class="support-quick" id="supportQuick">
      <div class="section-head"><h2>QUICK LINKS</h2><p>公式Web買取表・相場確認</p></div>
      <div class="shop-grid">{support_html}</div>
    </section>

    {timeline_section}

    <div class="section-head"><h2>STORE LIST</h2><p>簡易一覧</p></div>
    <div class="store-list" id="shopGrid">{cards_html}</div>

    <div class="section-head" id="supportLinks"><h2>SUPPORT LINKS</h2><p>公式Web買取表・相場確認</p></div>
    <div class="shop-grid">{support_html}</div>
  </main>
</div>

<script>
var selectedTypes = [];
var selectedBrands = [];
var selectedSort = 'latest';
var timelineItems = {json_for_script(timeline_items)};

function hasValue(list, value) {{
  return list.indexOf(value) !== -1;
}}

function addValue(list, value) {{
  if (!hasValue(list, value)) list.push(value);
}}

function removeValue(list, value) {{
  var index = list.indexOf(value);
  if (index !== -1) list.splice(index, 1);
}}

function eachNode(selector, callback) {{
  var nodes = document.querySelectorAll(selector);
  for (var i = 0; i < nodes.length; i++) callback(nodes[i], i);
}}

function escapeHtml(value) {{
  return String(value || '').replace(/[&<>"']/g, function (char) {{
    return {{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[char];
  }});
}}

function toggleType(type, button) {{
  var allTypeButton = document.querySelector('#typeRow .filter-chip');
  if (type === 'all') {{
    selectedTypes = [];
    eachNode('#typeRow .filter-chip', function (btn) {{ btn.classList.remove('active'); }});
    button.classList.add('active');
    applyFilters();
    return;
  }}

  if (allTypeButton) allTypeButton.classList.remove('active');

  if (hasValue(selectedTypes, type)) {{
    removeValue(selectedTypes, type);
    button.classList.remove('active');
  }} else {{
    addValue(selectedTypes, type);
    button.classList.add('active');
  }}

  if (selectedTypes.length === 0 && allTypeButton) allTypeButton.classList.add('active');
  applyFilters();
}}

function toggleBrand(brand, button) {{
  if (hasValue(selectedBrands, brand)) {{
    removeValue(selectedBrands, brand);
    button.classList.remove('active');
  }} else {{
    addValue(selectedBrands, brand);
    button.classList.add('active');
  }}
  applyFilters();
}}

function setSort(mode, button) {{
  selectedSort = mode;
  eachNode('#sortRow .filter-chip', function (btn) {{ btn.classList.remove('active'); }});
  button.classList.add('active');
  updateFilterSummary();
  renderTimeline();
}}

function resetFilters() {{
  selectedTypes = [];
  selectedBrands = [];
  selectedSort = 'latest';
  document.getElementById('searchInput').value = '';
  document.getElementById('compactSearchInput').value = '';
  eachNode('.sticky-search .filter-chip', function (btn) {{ btn.classList.remove('active'); }});
  var allTypeButton = document.querySelector('#typeRow .filter-chip');
  var latestButton = document.querySelector('#sortRow .filter-chip');
  if (allTypeButton) allTypeButton.classList.add('active');
  if (latestButton) latestButton.classList.add('active');
  applyFilters();
}}

function toggleFilterPanel() {{
  var panel = document.getElementById('filterPanel');
  if (panel) panel.classList.toggle('open');
}}

function updateFilterSummary() {{
  var typeText = selectedTypes.length === 0 ? 'すべて' : selectedTypes.length + 'タイプ選択中';
  var brandText = selectedBrands.length === 0 ? '' : ' / ' + selectedBrands.length + 'ブランド選択中';
  var sortLabels = {{latest:'新着順', x_post_box:'BOX優先', x_post_fixed:'定額優先', x_post_psa:'PSA優先', x_post_single:'シングル優先', shop_name:'店舗名順'}};
  var summary = document.getElementById('filterSummary');
  if (summary) summary.textContent = typeText + brandText + '・' + (sortLabels[selectedSort] || '新着順');
}}

function applyFilters() {{
  var search = document.getElementById('searchInput').value.replace(/^\\s+|\\s+$/g, '').toLowerCase();
  var cards = document.querySelectorAll('#shopGrid .shop-card');
  var count = 0;

  for (var i = 0; i < cards.length; i++) {{
    var card = cards[i];
    var typeList = (card.getAttribute('data-types') || '').split(' ');
    var brand = card.getAttribute('data-brand') || '';
    var searchText = (card.getAttribute('data-search') || '').toLowerCase();
    var typeOk = selectedTypes.length === 0;

    for (var t = 0; t < typeList.length; t++) {{
      if (hasValue(selectedTypes, typeList[t])) typeOk = true;
    }}

    var brandOk = selectedBrands.length === 0 || hasValue(selectedBrands, brand);
    var searchOk = !search || searchText.indexOf(search) !== -1;

    if (typeOk && brandOk && searchOk) {{
      card.classList.remove('hidden');
      count++;
    }} else {{
      card.classList.add('hidden');
    }}
  }}

  document.getElementById('resultCount').textContent = count;
  updateFilterSummary();
  renderTimeline();
}}

function renderTimeline() {{
  var search = document.getElementById('searchInput').value.replace(/^\\s+|\\s+$/g, '').toLowerCase();
  var items = [];

  for (var i = 0; i < timelineItems.length; i++) {{
    var item = timelineItems[i];
    var brandOk = selectedBrands.length === 0 || hasValue(selectedBrands, item.brand_id);
    var typeOk = selectedTypes.length === 0 || hasValue(selectedTypes, item.type_key);
    var searchOk = !search || String(item.search || '').toLowerCase().indexOf(search) !== -1;
    if (brandOk && typeOk && searchOk) items.push(item);
  }}

  if (selectedSort === 'shop_name') {{
    items.sort(function (a, b) {{ return String(a.shop_name || '').localeCompare(String(b.shop_name || ''), 'ja'); }});
  }} else if (selectedSort === 'latest') {{
    items.sort(function (a, b) {{ return Number(b.status_id || 0) - Number(a.status_id || 0); }});
  }} else {{
    items.sort(function (a, b) {{
      var priority = (b.type_key === selectedSort ? 1 : 0) - (a.type_key === selectedSort ? 1 : 0);
      return priority || (Number(b.status_id || 0) - Number(a.status_id || 0));
    }});
  }}

  if (items.length === 0) {{
    document.getElementById('timelineGrid').innerHTML = '<div class="link-card"><p class="summary">該当投稿はありません。</p></div>';
    return;
  }}

  var html = '';
  for (var j = 0; j < items.length; j++) {{
    var row = items[j];
    var shopName = escapeHtml(row.shop_name);
    var imagePart = row.image_url
      ? '<img src="' + escapeHtml(row.image_url) + '" alt="' + shopName + '">'
      : '<div class="no-thumb">NO IMAGE</div>';
    html += '<article class="shop-card">'
      + '<div class="thumb-wrap">' + imagePart + '</div>'
      + '<div class="shop-body">'
      + '<div class="card-meta"><span>𝕏</span><span>' + escapeHtml(row.type_label) + '</span></div>'
      + '<h3>' + shopName + '</h3>'
      + '<div class="summary">' + escapeHtml(row.updated_info || '更新情報なし') + ' / ' + escapeHtml(row.summary) + '</div>'
      + '<div class="badges"><span class="badge">' + escapeHtml(row.type_label) + '</span></div>'
      + '</div>'
      + '<div class="card-footer"><a href="stores/' + encodeURIComponent(row.shop_slug) + '.html">店舗ページ</a> / <a href="' + escapeHtml(row.tweet_url) + '" target="_blank" rel="noopener noreferrer">元投稿</a></div>'
      + '</article>';
  }}
  document.getElementById('timelineGrid').innerHTML = html;
}}

function toggleMenu() {{
  var panel = document.getElementById('menuPanel');
  if (panel) panel.classList.toggle('open');
}}

function updateCompactSearch() {{
  var compact = document.getElementById('compactSearch');
  var hero = document.getElementById('heroArea');
  if (!compact || !hero) return;
  if (hero.getBoundingClientRect().bottom < 0) compact.classList.add('visible');
  else compact.classList.remove('visible');
}}

document.addEventListener('DOMContentLoaded', function () {{
  var searchInput = document.getElementById('searchInput');
  var compactInput = document.getElementById('compactSearchInput');
  if (searchInput) {{
    searchInput.addEventListener('input', function () {{
      if (compactInput) compactInput.value = searchInput.value;
      applyFilters();
    }});
  }}
  if (compactInput) {{
    compactInput.addEventListener('input', function () {{
      if (searchInput) searchInput.value = compactInput.value;
      applyFilters();
    }});
  }}
  window.addEventListener('scroll', updateCompactSearch);
  updateCompactSearch();
  applyFilters();
}});
</script>
"""
    return html_shell("CardRadar｜大阪日本橋のポケカ買取情報", content)


# =========================
# ページ生成：店舗ページ
# =========================

def build_store_page(shop, posts_by_source, updated_at):
    sources = get_sources_by_shop(shop["shop_slug"])
    posts = get_posts_for_shop(posts_by_source, shop["shop_slug"])

    media_items = {}
    sections_html = ""

    for source in sources:
        if not is_x_source(source):
            continue

        source_posts = posts_by_source.get(source["id"], [])
        meta = TYPE_META[source["source_type"]]

        images_html = ""

        media_index = 0

        for post in source_posts:
            image_urls = post.get("image_urls", [])

            for image_url in image_urls:
                media_id = f'{source["id"]}_{post["status_id"]}_{media_index}'
                media_index += 1

                media_items[media_id] = {
                    "image_url": image_url,
                    "tweet_url": post["tweet_url"],
                    "summary": post["summary"],
                    "type_label": meta["label"],
                }

                images_html += f"""
<div class="image-card" onclick="openMedia('{h(media_id)}')">
  <img src="{h(image_url)}" alt="{h(shop["shop_name"])}の買取表画像">
  <div class="image-info">
    <p>{h(post["summary"])}</p>
    <small>{h(meta["label"])} / 画像{len(image_urls)}枚</small>
  </div>
</div>
"""

        if not images_html:
            images_html = """
<div class="link-card">
  <p class="summary">該当する画像付き投稿が見つかりませんでした。</p>
</div>
"""

        sections_html += f"""
<section class="image-section">
  <h2>{h(meta["label"])}</h2>
  <div class="image-grid">
    {images_html}
  </div>
</section>
"""

    support_html = ""

    for source in sources:
        if source["source_type"] not in ["official_price_list", "market_price_link"]:
            continue

        meta = TYPE_META[source["source_type"]]

        support_html += f"""
<section class="image-section">
  <h2>{h(meta["label"])}</h2>
  <div class="link-card">
    <h3>{h(source["shop_name"])}</h3>
    <p class="summary">{h(source["description"])}</p>
    <a href="{h(source["official_url"])}" target="_blank" rel="noopener noreferrer">ページを開く →</a>
  </div>
</section>
"""

    media_json = json_for_script(media_items)

    content = f"""
<div class="page-shell">
  <section class="hero">
    {logo_html("../")}

    <div class="breadcrumb">
      <a href="../index.html">TOP</a> /
      <a href="../osaka.html">OSAKA</a> /
      <a href="../osaka-nihonbashi.html">NIHONBASHI</a> /
      STORE
    </div>
  </section>

  <main class="store-layout">
    <div class="store-header">
      <h1 class="store-title">{h(shop["shop_name"])}</h1>
      <div class="store-sub">{h(shop["brand"])} / {h(shop["area"])}</div>
      <p class="area-description">
        この店舗の買取表画像を大きく表示しています。
        画像をタップすると拡大表示し、必要な場合のみX埋め込みを読み込みます。
      </p>
      <div class="updated">LAST UPDATE : {h(updated_at)}</div>
    </div>

    {sections_html}
    {support_html}
  </main>
</div>

<div class="modal" id="mediaModal">
  <div class="modal-inner">
    <button class="modal-close" onclick="closeMedia()">閉じる</button>

    <img class="modal-image" id="modalImage" src="" alt="買取表画像">

    <div class="modal-summary" id="modalSummary"></div>

    <div class="modal-actions">
      <a id="modalTweetLink" href="#" target="_blank" rel="noopener noreferrer">元投稿をXで開く</a>
      <button onclick="loadTweetEmbed()">X埋め込みを表示</button>
    </div>

    <div class="tweet-embed" id="tweetEmbed"></div>
  </div>
</div>

<script async src="https://platform.twitter.com/widgets.js"></script>

<script>
const MEDIA_ITEMS = {media_json};
let currentTweetUrl = "";

function openMedia(id) {{
  const item = MEDIA_ITEMS[id];

  if (!item) return;

  currentTweetUrl = item.tweet_url;

  document.getElementById("modalImage").src = item.image_url;
  document.getElementById("modalSummary").textContent = item.summary;
  document.getElementById("modalTweetLink").href = item.tweet_url;
  document.getElementById("tweetEmbed").innerHTML = "";

  document.getElementById("mediaModal").classList.add("open");
}}

function closeMedia() {{
  document.getElementById("mediaModal").classList.remove("open");
  document.getElementById("tweetEmbed").innerHTML = "";
}}

function loadTweetEmbed() {{
  if (!currentTweetUrl) return;

  const embed = document.getElementById("tweetEmbed");

  embed.innerHTML = `
    <blockquote class="twitter-tweet">
      <a href="${{currentTweetUrl}}"></a>
    </blockquote>
  `;

  if (window.twttr && window.twttr.widgets) {{
    window.twttr.widgets.load(embed);
  }}
}}
</script>
"""
    return html_shell(f"CardRadar｜{shop['shop_name']}", content, base_prefix="../")


# =========================
# X取得
# =========================

def collect_posts():
    posts_by_source = {}
    all_data = []
    updated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    if importlib.util.find_spec("playwright") is None:
        print("Playwrightが見つからないため、既存のdata.jsonからページを再生成します。")
        data_path = Path("data.json")
        if data_path.exists():
            with open(data_path, "r", encoding="utf-8") as f:
                all_data = json.load(f)

            for post in all_data:
                source_id = post.get("source_id")
                if source_id:
                    posts_by_source.setdefault(source_id, []).append(post)

            for posts in posts_by_source.values():
                posts.sort(key=lambda p: p.get("status_id", 0), reverse=True)

        return posts_by_source, all_data, updated_at

    sync_playwright = importlib.import_module("playwright.sync_api").sync_playwright

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
            posts_by_source[source["id"]] = []

            print("")
            print("==============================")
            print(source["shop_name"], "/", TYPE_META[source["source_type"]]["label"])
            print("==============================")

            if not is_x_source(source):
                data_item = {
                    **source,
                    "buy_type_label": TYPE_META[source["source_type"]]["label"],
                    "collected_at": updated_at,
                }
                all_data.append(data_item)
                print("リンク情報として保存")
                continue

            candidates = []
            seen_urls = set()

            try:
                page.goto(source["url"], wait_until="domcontentloaded", timeout=60000)
                time.sleep(10)

                page.wait_for_selector("article", timeout=30000)

                for _ in range(6):
                    page.mouse.wheel(0, 1400)
                    time.sleep(3)

                tweets = page.locator("article")
                count = tweets.count()

                print("検出article数:", count)

                for i in range(min(count, CHECK_POSTS_PER_SOURCE)):
                    tweet = tweets.nth(i)

                    text = tweet.inner_text()
                    url = get_status_url(tweet)

                    if not url:
                        continue

                    if url in seen_urls:
                        continue

                    if not is_target_post(text, source["source_type"]):
                        continue

                    image_urls = get_image_urls(tweet)

                    if not image_urls and "買取" not in text:
                        continue

                    seen_urls.add(url)

                    post = {
                        "source_id": source["id"],
                        "source_type": source["source_type"],
                        "buy_type_label": TYPE_META[source["source_type"]]["label"],
                        "shop_name": source["shop_name"],
                        "shop_slug": source["shop_slug"],
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

                posts_by_source[source["id"]] = posts
                all_data.extend(posts)

                print("採用:", len(posts))

            except Exception as e:
                print("取得エラー:", e)

        browser.close()

    return posts_by_source, all_data, updated_at


# =========================
# ファイル保存
# =========================

def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def build_all_pages(posts_by_source, updated_at):
    write_file("index.html", build_index_page(updated_at))
    write_file("osaka.html", build_osaka_page(updated_at))
    write_file("osaka-nihonbashi.html", build_area_page(posts_by_source, updated_at))

    shops = get_physical_shops("osaka-nihonbashi")

    for shop in shops:
        store_html = build_store_page(shop, posts_by_source, updated_at)
        write_file(STORES_DIR / f"{shop['shop_slug']}.html", store_html)


def main():
    posts_by_source, all_data, updated_at = collect_posts()

    build_all_pages(posts_by_source, updated_at)

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print("")
    print("================================")
    print("生成完了")
    print("index.html")
    print("osaka.html")
    print("osaka-nihonbashi.html")
    print("stores/*.html")
    print("data.json")
    print("================================")


if __name__ == "__main__":
    main()

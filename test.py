from playwright.sync_api import sync_playwright
import time
import re
import json
import sys
import argparse
import html as html_lib
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import quote


# =========================
# 基本設定
# =========================

USER_DATA_DIR = "userdata"
Path(USER_DATA_DIR).mkdir(exist_ok=True)

STORES_DIR = Path("stores")
STORES_DIR.mkdir(exist_ok=True)

SAFETY_POSTS_PER_SOURCE = 20
FALLBACK_POSTS_PER_SOURCE = 5
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

MAIN_FILTER_TYPES = [
    "x_post_single",
    "x_post_box",
    "x_post_fixed",
    "x_post_psa",
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


def contains_any(text, words):
    lower_text = text.lower()
    return any(word.lower() in lower_text for word in words)


def matching_words(text, words):
    lower_text = text.lower()
    return [word for word in words if word.lower() in lower_text]


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

    if contains_any(text, ng_words):
        return False

    if not contains_any(text, pokemon_words):
        return False

    return contains_any(text, buy_words)


def classify_display_type(text, source_type):
    psa_words = ["PSA", "PSA10", "PSA9", "PSA 10", "PSA 9", "鑑定品", "鑑定", "ARS", "BGS", "ケース付き", "グレーディング"]
    psa_ng_words = ["PSA買取不可", "PSA対象外", "PSAは対象外", "PSA買取なし"]
    fixed_words = ["定額", "一律", "最低保証", "保証買取", "まとめ買取", "RR定額", "AR定額", "SR定額", "UR定額", "ノーマル買取", "ノーマル", "ストレージ", "汎用", "大量買取"]
    box_words = ["BOX", "box", "未開封", "シュリンク", "カートン", "1BOX", "ボックス", "パック", "パック買取", "未開封BOX", "未開封買取"]
    box_ng_words = ["BOX以外", "BOX買取以外", "ボックス以外", "未開封BOX以外", "BOX対象外", "BOXは対象外", "BOX買取なし"]

    if not contains_any(text, psa_ng_words):
        matches = matching_words(text, psa_words)
        if matches:
            return "x_post_psa", ",".join(matches)

    matches = matching_words(text, fixed_words)
    if matches:
        return "x_post_fixed", ",".join(matches)

    if not contains_any(text, box_ng_words):
        matches = matching_words(text, box_words)
        if matches:
            return "x_post_box", ",".join(matches)

    if source_type in TYPE_META and source_type.startswith("x_post_"):
        return source_type, "source_type fallback"

    return "x_post_single", "default single"


def display_type_label(display_type):
    return short_type_label(TYPE_META.get(display_type, TYPE_META["x_post_single"])["label"])


def parse_posted_at(value):
    if not value:
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone(timedelta(hours=9)))
    except ValueError:
        return None


def posted_date_from_values(posted_at, collected_at):
    parsed = parse_posted_at(posted_at)
    if parsed:
        return parsed.strftime("%Y-%m-%d")
    if collected_at:
        try:
            return datetime.strptime(collected_at, "%Y/%m/%d %H:%M").strftime("%Y-%m-%d")
        except ValueError:
            pass
    return ""


def get_posted_at(tweet):
    times = tweet.locator("time")
    if times.count() == 0:
        return ""
    return times.nth(0).get_attribute("datetime") or ""


def normalize_post(item, source=None):
    post = dict(item)
    if source:
        for key in ["source_id", "source_type", "shop_name", "shop_slug", "brand", "brand_id", "area", "area_id"]:
            if not post.get(key):
                source_key = "id" if key == "source_id" else key
                post[key] = source.get(source_key, post.get(key, ""))

    source_type = post.get("source_type") or (source or {}).get("source_type", "x_post_single")
    post["source_type"] = source_type
    text_for_class = post.get("full_text") or post.get("summary") or ""
    display_type, reason = classify_display_type(text_for_class, source_type)
    post["display_type"] = post.get("display_type") or display_type
    post["display_type_label"] = post.get("display_type_label") or display_type_label(post["display_type"])
    post["buy_type_label"] = post.get("buy_type_label") or TYPE_META.get(source_type, TYPE_META["x_post_single"])["label"]
    post["posted_at"] = post.get("posted_at") or ""
    post["posted_date_jst"] = post.get("posted_date_jst") or posted_date_from_values(post.get("posted_at"), post.get("collected_at"))
    post["classify_reason"] = post.get("classify_reason") or reason
    post["image_urls"] = post.get("image_urls") or []
    post["image_count"] = len(post["image_urls"])
    post["status_id"] = post.get("status_id") or get_status_id(post.get("tweet_url", ""))
    return post


def select_latest_posts(candidates):
    candidates = [normalize_post(post) for post in candidates]
    candidates.sort(key=sort_post_key, reverse=True)
    posted_candidates = [post for post in candidates if parse_posted_at(post.get("posted_at")) and post.get("posted_date_jst")]
    if posted_candidates:
        latest_date = max(post["posted_date_jst"] for post in posted_candidates)
        latest_day_posts = [post for post in candidates if post.get("posted_date_jst") == latest_date]
        return latest_day_posts[:SAFETY_POSTS_PER_SOURCE]
    return candidates[:FALLBACK_POSTS_PER_SOURCE]


def dedupe_data_items(items):
    deduped = []
    seen_posts = set()
    for item in items:
        source_id = item.get("source_id") or item.get("id") or ""
        tweet_url = item.get("tweet_url") or ""
        if source_id and tweet_url:
            key = (source_id, tweet_url)
            if key in seen_posts:
                continue
            seen_posts.add(key)
        deduped.append(item)
    return deduped


def sort_post_key(post):
    return (post.get("posted_at") or "", post.get("status_id", 0))


def get_posts_for_shop(posts_by_source, shop_slug):
    posts = []

    for source in get_sources_by_shop(shop_slug):
        posts.extend(normalize_post(post, source) for post in posts_by_source.get(source["id"], []))

    posts.sort(key=sort_post_key, reverse=True)
    return posts


def get_latest_post(posts):
    if not posts:
        return None

    return sorted(posts, key=sort_post_key, reverse=True)[0]


def first_image(posts):
    for post in posts:
        for image_url in post.get("image_urls", []):
            return image_url
    return None

def get_timeline_posts(posts_by_source, area_id):
    posts_by_key = {}

    for source_posts in posts_by_source.values():
        for raw_post in source_posts:
            post = normalize_post(raw_post)
            if post.get("area_id") != area_id:
                continue
            if not post.get("tweet_url"):
                continue
            if not post.get("image_urls"):
                continue

            key = post.get("tweet_url") or post.get("status_id")
            if key not in posts_by_key:
                merged = dict(post)
                merged["image_urls"] = []
                posts_by_key[key] = merged

            merged = posts_by_key[key]
            for image_url in post.get("image_urls", []):
                if image_url not in merged["image_urls"]:
                    merged["image_urls"].append(image_url)

            if infer_type_priority(post.get("display_type")) < infer_type_priority(merged.get("display_type")):
                for field in ["display_type", "display_type_label", "source_id", "classify_reason"]:
                    if field in post:
                        merged[field] = post[field]

    posts = list(posts_by_key.values())
    posts.sort(key=sort_post_key, reverse=True)
    return posts


def short_type_label(label_or_type):
    mapping = {
        "x_post_single": "シングル", "x_post_box": "BOX", "x_post_fixed": "定額", "x_post_psa": "PSA",
        "official_price_list": "公式Web", "market_price_link": "相場",
        "シングル買取": "シングル", "BOX買取": "BOX", "定額買取": "定額", "PSA買取": "PSA",
        "公式Web買取表": "公式Web", "相場確認": "相場",
    }
    return mapping.get(label_or_type, label_or_type or "買取")


def infer_type_priority(source_type):
    order = {
        "x_post_psa": 0,
        "x_post_fixed": 1,
        "x_post_box": 2,
        "x_post_single": 3,
    }
    return order.get(source_type, 9)


def infer_display_type(post):
    return normalize_post(post).get("display_type", post.get("source_type", "x_post_single"))


def format_update_label(value):
    if not value:
        return "未取得"
    parsed = parse_posted_at(value)
    if parsed:
        return parsed.strftime("%m/%d %H:%M")
    try:
        return datetime.strptime(value, "%Y/%m/%d %H:%M").strftime("%m/%d %H:%M")
    except ValueError:
        return value


def format_date_label(value):
    if not value:
        return "未取得"
    try:
        return datetime.strptime(value, "%Y-%m-%d").strftime("%m/%d")
    except ValueError:
        return value


def short_summary(value, limit=90):
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else text[:limit] + "..."


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
  position: static;
  top: auto;
  z-index: auto;
  background: rgba(5,5,5,.92);
  backdrop-filter: blur(18px);
  border-top: 1px solid rgba(255,255,255,.08);
  border-bottom: 1px solid rgba(255,255,255,.10);
  padding: 14px 7vw;
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

.search-area,
.compact-search-bar {
  background: rgba(5,5,5,.92);
  backdrop-filter: blur(18px);
  border-top: 1px solid rgba(255,255,255,.08);
  border-bottom: 1px solid rgba(255,255,255,.10);
  padding: 10px 7vw;
}

.search-area {
  position: static;
  top: auto;
  z-index: auto;
}

.compact-search-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 80;
  transform: translateY(-105%);
  opacity: 0;
  pointer-events: none;
  transition: transform .18s ease, opacity .18s ease;
}

.compact-search-bar.search-visible {
  transform: translateY(0);
  opacity: 1;
  pointer-events: auto;
}

.search-line,
.compact-line {
  display: grid;
  gap: 8px;
  align-items: center;
}

.search-line {
  grid-template-columns: minmax(0, 1fr) auto;
}

.compact-line {
  grid-template-columns: 42px minmax(0, 1fr) auto;
}

.tool-button,
.filter-toggle,
.sort-select {
  height: 36px;
  border: 1px solid rgba(255,255,255,.16);
  background: rgba(255,255,255,.055);
  color: white;
  padding: 0 12px;
  font-size: 13px;
}

.tool-button,
.filter-toggle { cursor: pointer; }

.tool-button.menu-button {
  width: 42px;
  padding: 0;
  font-size: 20px;
  line-height: 1;
}

.search-input {
  width: 100%;
  height: 36px;
  min-width: 0;
  background: rgba(255,255,255,.075);
  border: 1px solid rgba(255,255,255,.16);
  color: white;
  padding: 0 12px;
  font-size: 14px;
  outline: none;
}

.type-row,
.control-row,
.brand-panel,
.support-quick-links {
  margin-top: 7px;
}

.type-row,
.brand-row,
.support-quick-links {
  display: flex;
  gap: 7px;
  overflow-x: auto;
  padding-bottom: 3px;
}

.control-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 8px;
  align-items: center;
}

.sort-wrap {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 8px;
  align-items: center;
  color: rgba(255,255,255,.62);
  font-size: 12px;
}

.sort-select { width: 100%; appearance: auto; }

.brand-panel {
  display: none;
  border-top: 1px solid rgba(255,255,255,.09);
  padding-top: 8px;
}

.search-area.filters-open .brand-panel { display: block; }

.support-quick-links {
  flex-wrap: wrap;
  align-items: center;
  color: rgba(255,255,255,.50);
  font-size: 12px;
}

.support-quick-links a {
  color: rgba(255,255,255,.72);
  text-decoration: none;
  border: 1px solid rgba(255,255,255,.13);
  padding: 7px 9px;
  font-size: 12px;
}

.reset-button {
  height: 34px;
  margin-top: 8px;
}

.result-line {
  margin-top: 0;
  white-space: nowrap;
  color: rgba(255,255,255,.58);
  font-size: 12px;
  letter-spacing: .06em;
}

.view-switch {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.view-toggle {
  min-height: 34px;
  border: 1px solid rgba(255,255,255,.16);
  background: rgba(255,255,255,.045);
  color: rgba(255,255,255,.76);
  cursor: pointer;
}

.view-toggle.active {
  border-color: rgba(255,255,255,.34);
  background: rgba(255,255,255,.13);
  color: white;
}

.view-panel.hidden {
  display: none !important;
}

.timeline-list {
  max-width: 760px;
  display: grid;
  gap: 26px;
}

.timeline-post {
  background: rgba(14,14,14,.96);
  border: 1px solid rgba(255,255,255,.20);
  box-shadow: 0 20px 48px rgba(0,0,0,.34);
  padding: 13px;
}

.timeline-head {
  display: block;
}

.timeline-store {
  font-size: 16px;
  font-weight: 650;
  letter-spacing: .04em;
}

.timeline-meta {
  margin-top: 5px;
  color: rgba(255,255,255,.58);
  font-size: 12px;
  line-height: 1.6;
}

.timeline-type {
  color: rgba(255,255,255,.86);
  margin-left: 8px;
}

.timeline-images {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-top: 10px;
}

.store-post-image-list {
  display: flex;
  gap: 10px;
  margin-top: 10px;
  overflow-x: auto;
  overscroll-behavior-x: contain;
  scroll-snap-type: x mandatory;
  padding-bottom: 6px;
}

.store-post-image-list .store-post-image {
  flex: 0 0 100%;
  scroll-snap-align: start;
}

.timeline-image {
  position: relative;
  display: block;
  width: 100%;
  background: rgba(255,255,255,.045);
  border: 1px solid rgba(255,255,255,.12);
  overflow: hidden;
  cursor: zoom-in;
  padding: 0;
}

.timeline-image img {
  width: 100%;
  display: block;
}

.zoom-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(0,0,0,.74);
  border: 1px solid rgba(255,255,255,.24);
  color: white;
  padding: 5px 8px;
  font-size: 12px;
}

.timeline-actions {
  margin-top: 10px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 7px;
}

.timeline-actions a,
.timeline-actions button {
  min-height: 34px;
  text-decoration: none;
  border: 1px solid rgba(255,255,255,.18);
  background: rgba(255,255,255,.045);
  padding: 8px 6px;
  font-size: 12px;
  color: rgba(255,255,255,.88);
  text-align: center;
  cursor: pointer;
}

.simple-store-list { max-width: 760px; display: grid; gap: 10px; }

.store-group-list {
  max-width: 100%;
  display: grid;
  gap: 28px;
}

.store-group {
  border: 1px solid rgba(255,255,255,.16);
  background: rgba(10,10,10,.90);
  padding: 14px;
}

.store-group-head {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
  align-items: start;
  margin-bottom: 12px;
}

.store-group-name {
  font-size: 16px;
  font-weight: 650;
}

.store-group-meta {
  margin-top: 5px;
  color: rgba(255,255,255,.58);
  font-size: 12px;
  line-height: 1.6;
}

.store-group-link {
  color: rgba(255,255,255,.82);
  text-decoration: none;
  border: 1px solid rgba(255,255,255,.16);
  padding: 8px 10px;
  font-size: 12px;
  white-space: nowrap;
}

.store-post-strip {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  overscroll-behavior-x: contain;
  scroll-snap-type: x mandatory;
  padding-bottom: 8px;
}

.store-post-card {
  flex: 0 0 min(88vw, 520px);
  scroll-snap-align: start;
  border: 1px solid rgba(255,255,255,.13);
  background: rgba(255,255,255,.035);
  padding: 10px;
}

.store-post-meta {
  color: rgba(255,255,255,.70);
  font-size: 12px;
  margin-bottom: 8px;
}

.store-post-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 7px;
  margin-top: 8px;
}

.store-post-actions a,
.store-post-actions button {
  min-height: 34px;
  border: 1px solid rgba(255,255,255,.18);
  background: rgba(255,255,255,.045);
  color: rgba(255,255,255,.88);
  text-align: center;
  text-decoration: none;
  font-size: 12px;
  cursor: pointer;
}

@media (min-width: 820px) {
  .store-post-card {
    flex-basis: min(48%, 520px);
  }
}

.simple-store-card {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
  align-items: center;
  text-decoration: none;
  background: rgba(10,10,10,.82);
  border: 1px solid rgba(255,255,255,.13);
  padding: 15px 16px;
}

.simple-store-card.is-waiting {
  opacity: .62;
  border-style: dashed;
}

.simple-store-name { font-weight: 650; font-size: 15px; }
.simple-store-meta { margin-top: 6px; color: rgba(255,255,255,.56); font-size: 12px; line-height: 1.6; }
.simple-store-date { color: rgba(255,255,255,.58); font-size: 12px; white-space: nowrap; }

.image-count {
  position: absolute;
  left: 8px;
  bottom: 8px;
  background: rgba(0,0,0,.72);
  border: 1px solid rgba(255,255,255,.22);
  color: white;
  padding: 5px 8px;
  font-size: 12px;
}

.modal-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-top: 12px;
}

.modal-nav button {
  min-height: 38px;
  border: 1px solid rgba(255,255,255,.18);
  background: rgba(255,255,255,.045);
  color: white;
  padding: 8px 12px;
  cursor: pointer;
}

.modal-counter {
  color: rgba(255,255,255,.62);
  font-size: 13px;
}

.store-toggle {
  width: 100%;
  margin-top: 8px;
  min-height: 36px;
  border: 1px solid rgba(255,255,255,.16);
  background: rgba(255,255,255,.045);
  color: rgba(255,255,255,.88);
  cursor: pointer;
}

.store-panel {
  display: none;
  margin-top: 8px;
  border-top: 1px solid rgba(255,255,255,.09);
  padding-top: 8px;
}

.search-area:not(.stores-open) .store-panel {
  display: none !important;
}

.search-area.stores-open .store-panel {
  display: grid;
  gap: 8px;
}

.store-panel-card {
  display: grid;
  gap: 5px;
  color: inherit;
  text-decoration: none;
  border: 1px solid rgba(255,255,255,.11);
  background: rgba(255,255,255,.035);
  padding: 11px 12px;
}

.store-panel-card.is-waiting {
  opacity: .62;
  border-style: dashed;
}

.store-panel-name {
  font-weight: 650;
}

.store-panel-meta,
.store-panel-link {
  color: rgba(255,255,255,.58);
  font-size: 12px;
}

.store-panel-link {
  margin-top: 2px;
}

.support-groups {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.support-group {
  background: rgba(8,8,8,.82);
  border: 1px solid rgba(255,255,255,.11);
  padding: 16px;
}

.support-group h3 {
  margin: 0 0 10px;
  font-size: 15px;
}

.support-group a {
  display: block;
  color: rgba(255,255,255,.78);
  text-decoration: none;
  padding: 8px 0;
  border-top: 1px solid rgba(255,255,255,.08);
}

.nav-overlay {
  position: fixed;
  inset: 0;
  z-index: 320;
  display: none;
  background: rgba(0,0,0,.68);
  backdrop-filter: blur(8px);
}

.nav-overlay.open { display: block; }

.nav-panel {
  width: min(86vw, 340px);
  min-height: 100%;
  background: rgba(7,7,7,.98);
  border-right: 1px solid rgba(255,255,255,.16);
  box-shadow: 22px 0 48px rgba(0,0,0,.44);
  padding: 18px;
}

.nav-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 18px;
}

.nav-title {
  letter-spacing: .18em;
  font-size: 13px;
  color: rgba(255,255,255,.72);
}

.nav-close {
  width: 42px;
  height: 42px;
  border: 1px solid rgba(255,255,255,.16);
  background: rgba(255,255,255,.05);
  color: white;
  cursor: pointer;
  font-size: 20px;
}

.nav-links {
  display: grid;
  gap: 8px;
}

.nav-links a {
  display: block;
  text-decoration: none;
  color: rgba(255,255,255,.88);
  border: 1px solid rgba(255,255,255,.11);
  background: rgba(255,255,255,.035);
  padding: 14px 13px;
  font-size: 15px;
}

main {
  padding: 28px 7vw calc(104px + env(safe-area-inset-bottom));
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

.no-result {
  max-width: 760px;
  margin: 14px auto 0;
  padding: 18px;
  border: 1px solid rgba(255,255,255,.13);
  background: rgba(255,255,255,.045);
  color: rgba(255,255,255,.72);
  text-align: center;
  line-height: 1.7;
}

@media (max-width: 1100px) {
  .shop-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .hero {
    padding: 30px 18px 24px;
  }

  .hero-large {
    padding: 30px 18px;
  }

  .selector-grid,
  .shop-grid,
  .image-grid {
    grid-template-columns: 1fr;
  }

  .search-main {
    grid-template-columns: 1fr;
  }

  .reset-button {
    width: 100%;
  }

  main {
    padding: 24px 18px calc(112px + env(safe-area-inset-bottom));
  }

  .section-head {
    display: block;
  }

  .search-area,
  .compact-search-bar {
    padding: 9px 14px;
  }

  .compact-line {
    grid-template-columns: 40px minmax(0, 1fr) auto;
    gap: 7px;
  }

  .timeline-post {
    padding: 12px;
  }

  .timeline-images {
    grid-template-columns: 1fr;
  }

  .timeline-head,
  .store-group-head,
  .simple-store-card {
    grid-template-columns: 1fr;
  }

  .store-post-card { flex-basis: 88vw; }

  .timeline-head {
    display: grid;
  }

  .simple-store-date {
    white-space: normal;
  }
  .support-groups {
    grid-template-columns: 1fr;
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
    timeline_posts = get_timeline_posts(posts_by_source, "osaka-nihonbashi")

    media_items = {}
    timeline_html = ""
    timeline_initial_count = len(timeline_posts)
    no_result_class = "no-result hidden" if timeline_initial_count else "no-result"
    no_result_attrs = ' hidden aria-hidden="true" style="display:none"' if timeline_initial_count else ' aria-hidden="false"'
    latest_timeline_date = timeline_posts[0].get("posted_date_jst", "") if timeline_posts else ""
    same_day_count = sum(1 for post in timeline_posts if post.get("posted_date_jst") == latest_timeline_date) if latest_timeline_date else len(timeline_posts)
    timeline_notice = f"最新日：{format_date_label(latest_timeline_date)} / 最新日の投稿：{same_day_count}件" if timeline_posts else "最新日：未取得 / 最新日の投稿：0件"

    for post in timeline_posts:
        post = normalize_post(post)
        image_urls = post.get("image_urls", [])
        display_type = post.get("display_type", infer_display_type(post))
        image_count = len(image_urls)
        image_html = """
  <div class="timeline-image no-thumb"><span class="zoom-badge">画像なし</span></div>
"""
        media_id = f'timeline_{post.get("source_id", "post")}_{post.get("status_id", 0)}'

        if image_urls:
            media_items[media_id] = {
                "image_urls": image_urls,
                "tweet_url": post["tweet_url"],
                "summary": short_summary(post.get("summary", "")),
                "shop_name": post["shop_name"],
                "type_label": short_type_label(display_type),
                "checked_at": format_update_label(post.get("posted_at") or post.get("collected_at", updated_at)),
            }
            image_buttons = []
            for image_index, image_url in enumerate(image_urls):
                image_buttons.append(f"""
    <button class="timeline-image" type="button" onclick="openTimelineMedia('{h(media_id)}', {image_index})">
      <img src="{h(image_url)}" alt="{h(post["shop_name"])}の買取表画像 {image_index + 1}" loading="lazy">
      <span class="zoom-badge">拡大</span>
      <span class="image-count">画像 {image_index + 1} / {image_count}</span>
    </button>
""")
            image_html = f"""
  <div class="timeline-images">
{''.join(image_buttons)}
  </div>
"""

        checked_label = format_update_label(post.get("posted_at") or post.get("collected_at", updated_at))
        type_label = short_type_label(display_type)

        timeline_html += f"""
<article class="timeline-post"
  data-status="{h(post.get("status_id", 0))}"
  data-store="{h(post.get("shop_name", ""))}"
  data-types="{h(display_type)}"
  data-brand="{h(post.get("brand_id", ""))}"
  data-search="{h(post.get("shop_name", "") + ' ' + post.get("brand", "") + ' ' + post.get("buy_type_label", "") + ' ' + type_label + ' ' + post.get("summary", ""))}"
>
  <div class="timeline-head">
    <div class="timeline-store">{h(post["shop_name"])}</div>
    <div class="timeline-meta">確認：{h(checked_label)}<span class="timeline-type">　{h(type_label)}</span></div>
  </div>

{image_html}

  <div class="timeline-actions">
    <button type="button" onclick="openTimelineMedia('{h(media_id)}')">拡大</button>
    <a href="stores/{h(post["shop_slug"])}.html">この店舗を見る</a>
    <a href="{h(post["tweet_url"])}" target="_blank" rel="noopener noreferrer">Xで開く</a>
  </div>
</article>
"""

    store_groups_html = ""

    for shop in shops:
        shop_posts = [normalize_post(post) for post in timeline_posts if post.get("shop_slug") == shop["shop_slug"]]
        if not shop_posts:
            continue

        latest_shop_date = max((post.get("posted_date_jst", "") for post in shop_posts), default="")
        latest_shop_posts = [post for post in shop_posts if not latest_shop_date or post.get("posted_date_jst", "") == latest_shop_date]
        latest_shop_posts.sort(key=lambda post: int(post.get("status_id", 0)), reverse=True)

        display_types = []
        for post in latest_shop_posts:
            display_type = post.get("display_type", infer_display_type(post))
            if display_type not in display_types:
                display_types.append(display_type)
        type_text = " / ".join(short_type_label(t) for t in display_types) if display_types else "未分類"
        latest_label = format_date_label(latest_shop_date) if latest_shop_date else "未取得"

        store_post_cards = ""
        for post in latest_shop_posts:
            image_urls = post.get("image_urls", [])
            if not image_urls:
                continue
            display_type = post.get("display_type", infer_display_type(post))
            type_label = short_type_label(display_type)
            media_id = f'timeline_{post.get("source_id", "post")}_{post.get("status_id", 0)}'
            image_count = len(image_urls)
            store_image_buttons = []
            for image_index, image_url in enumerate(image_urls):
                store_image_buttons.append(f"""
        <button class="timeline-image store-post-image" type="button" onclick="openTimelineMedia('{h(media_id)}', {image_index})">
          <img src="{h(image_url)}" alt="{h(post["shop_name"])}の買取表画像 {image_index + 1}" loading="lazy">
          <span class="zoom-badge">拡大</span>
          <span class="image-count">画像 {image_index + 1} / {image_count}</span>
        </button>
""")

            store_post_cards += f"""
      <article class="store-post-card"
        data-status="{h(post.get("status_id", 0))}"
        data-store="{h(post.get("shop_name", ""))}"
        data-types="{h(display_type)}"
        data-brand="{h(post.get("brand_id", ""))}"
        data-search="{h(post.get("shop_name", "") + ' ' + post.get("brand", "") + ' ' + post.get("buy_type_label", "") + ' ' + type_label + ' ' + post.get("summary", ""))}"
      >
        <div class="store-post-meta">{h(type_label)} / 画像 {image_count}枚</div>
        <div class="store-post-image-list">
{''.join(store_image_buttons)}
        </div>
        <div class="store-post-actions">
          <button type="button" onclick="openTimelineMedia('{h(media_id)}', 0)">拡大</button>
          <a href="{h(post["tweet_url"])}" target="_blank" rel="noopener noreferrer">Xで開く</a>
        </div>
      </article>
"""

        if not store_post_cards:
            continue

        store_groups_html += f"""
<section class="store-group"
  data-types="{h(' '.join(display_types))}"
  data-brand="{h(shop["brand_id"])}"
  data-search="{h(shop["shop_name"] + ' ' + shop["brand"] + ' ' + type_text)}"
>
  <div class="store-group-head">
    <div>
      <div class="store-group-name">{h(shop["shop_name"])}</div>
      <div class="store-group-meta">確認日：{h(latest_label)} / 投稿 {len(latest_shop_posts)}件 / {h(type_text)}</div>
    </div>
    <a class="store-group-link" href="stores/{h(shop["shop_slug"])}.html">この店舗を見る</a>
  </div>
  <div class="store-post-strip">
{store_post_cards}
  </div>
</section>
"""

    stores_active_html = ""
    stores_waiting_html = ""
    store_panel_active_html = ""
    store_panel_waiting_html = ""

    for shop in shops:
        posts = get_posts_for_shop(posts_by_source, shop["shop_slug"])
        latest = get_latest_post(posts)
        types = get_shop_types(shop["sources"])
        type_labels = [short_type_label(t) for t in types]
        latest_date = format_date_label(latest.get("posted_date_jst")) if latest else "未取得"
        latest_count = len(posts)
        type_text = " / ".join(type_labels)
        has_posts = latest_count > 0
        waiting_class = "" if has_posts else " is-waiting"
        post_count_label = f"{latest_date}投稿：{latest_count}件" if has_posts else "取得待ち"

        store_card_html = f"""
<a class="simple-store-card{waiting_class}"
   href="stores/{h(shop["shop_slug"])}.html"
   data-types="{' '.join(types)}"
   data-brand="{h(shop["brand_id"])}"
   data-search="{h(shop["shop_name"] + ' ' + shop["brand"] + ' ' + ' '.join(type_labels))}"
>
  <div>
    <div class="simple-store-name">{h(shop["shop_name"])}</div>
    <div class="simple-store-meta">{h(type_text)} / {h(post_count_label)}</div>
    <div class="store-panel-link">この店舗を見る →</div>
  </div>
</a>
"""

        store_panel_card_html = f"""
<a class="store-panel-card{waiting_class}" href="stores/{h(shop["shop_slug"])}.html">
  <div class="store-panel-name">{h(shop["shop_name"])}</div>
  <div class="store-panel-meta">{h(shop["brand"])} / {h(type_text)} / {h(post_count_label)}</div>
  <div class="store-panel-link">この店舗を見る →</div>
</a>
"""

        if has_posts:
            stores_active_html += store_card_html
            store_panel_active_html += store_panel_card_html
        else:
            stores_waiting_html += store_card_html
            store_panel_waiting_html += store_panel_card_html

    stores_html = stores_active_html + stores_waiting_html
    store_panel_html = store_panel_active_html + store_panel_waiting_html

    support_groups = {
        "official_price_list": {"title": "公式Web買取表", "items": []},
        "market_price_link": {"title": "相場確認", "items": []},
    }
    support_quick_links = """
<span>補助リンク：</span>
<a href="#support-links">公式Web買取表</a>
<a href="#support-links">相場確認</a>
"""

    for source in support_sources:
        group = support_groups.get(source["source_type"])
        if not group:
            continue
        group["items"].append(source)

    support_html = ""
    for key in ["official_price_list", "market_price_link"]:
        group = support_groups[key]
        links = "".join([
            f'<a href="{h(source["official_url"])}" target="_blank" rel="noopener noreferrer">{h(source["shop_name"])}</a>'
            for source in group["items"]
        ])
        support_html += f"""
<section class="support-group">
  <h3>{h(group["title"])}</h3>
  {links}
</section>
"""

    type_buttons = """
<button class="filter-chip active" data-type="all" onclick="toggleType('all', this)">すべて</button>
"""

    for type_key in MAIN_FILTER_TYPES:
        meta = TYPE_META[type_key]
        type_buttons += f"""
<button class="filter-chip" data-type="{h(type_key)}" onclick="toggleType('{h(type_key)}', this)">{h(short_type_label(meta["label"]))}</button>
"""

    brand_buttons = ""

    for brand in brands:
        brand_buttons += f"""
<button class="filter-chip" onclick="toggleBrand('{h(brand["id"])}', this)">{h(brand["label"])}</button>
"""

    media_json = json_for_script(media_items)

    content = f"""
<div class="page-shell">
  <section class="hero">
    {logo_html()}

    <div class="breadcrumb">
      <a href="index.html">TOP</a> / <a href="osaka.html">OSAKA</a> / NIHONBASHI
    </div>

    <h1 class="area-title">NIHONBASHI</h1>

    <p class="area-description">
      大阪・日本橋周辺のポケカ買取表画像を、新しい順に眺められるタイムラインです。
      店舗別の詳細は各投稿または店舗一覧から確認できます。
    </p>

    <div class="updated">LAST CHECK : {h(updated_at)}</div>
  </section>

  <div class="search-area" id="searchArea">
    <div class="search-line">
      <input id="searchInput" class="search-input" type="search" placeholder="店舗・カード名で検索">
      <div class="result-line">表示中：<span class="result-count">{timeline_initial_count}</span>件</div>
    </div>

    <div class="view-switch" role="group" aria-label="表示切替">
      <button id="timelineViewButton" class="view-toggle active" type="button" onclick="setViewMode('timeline')">新着TL</button>
      <button id="storeViewButton" class="view-toggle" type="button" onclick="setViewMode('store')">店舗ごと</button>
    </div>

    <div class="type-row">
      {type_buttons}
    </div>

    <div class="control-row">
      <label class="sort-wrap">並び替え
        <select id="sortSelect" class="sort-select" onchange="setSort(this.value)">
          <option value="new">新着順</option>
          <option value="box">BOX優先</option>
          <option value="fixed">定額優先</option>
          <option value="psa">PSA優先</option>
          <option value="single">シングル優先</option>
          <option value="store">店舗名順</option>
        </select>
      </label>
      <button class="filter-toggle" type="button" onclick="toggleFilters()">絞り込み</button>
    </div>

    <div class="support-quick-links">
      {support_quick_links}
    </div>

    <button class="store-toggle" type="button" onclick="toggleStorePanel()">店舗別で見る</button>

    <div class="brand-panel" id="brandPanel" aria-hidden="true">
      <div class="brand-row">
        {brand_buttons}
      </div>
      <button class="reset-button" onclick="resetFilters()">リセット</button>
    </div>

    <div class="store-panel" id="storePanel" aria-hidden="true">
      {store_panel_html}
    </div>
  </div>

  <div class="compact-search-bar" id="compactSearchBar">
    <div class="compact-line">
      <button class="tool-button menu-button" type="button" aria-label="メニュー" onclick="openMenu()">☰</button>
      <input id="compactSearchInput" class="search-input" type="search" placeholder="検索">
      <div class="result-line"><span class="result-count">{timeline_initial_count}</span>件</div>
    </div>
    <div class="type-row compact-type-row">
      {type_buttons}
    </div>
  </div>

  <main>
    <div id="timelineView" class="view-panel">
      <div class="section-head">
        <h2>TIMELINE</h2>
        <p>1ツイート1カードで表示 / {h(timeline_notice)}</p>
      </div>

      <div class="timeline-list" id="timelineList">
        {timeline_html}
      </div>
    </div>

    <div id="storeView" class="view-panel hidden">
      <div class="section-head">
        <h2>STORE VIEW</h2>
        <p>店舗ごとに最新日の投稿を横スライドで表示</p>
      </div>

      <div class="store-group-list" id="storeGroupList">
        {store_groups_html}
      </div>
    </div>

    <div class="{no_result_class}" id="noResult"{no_result_attrs}>該当する買取投稿はありません。<br>条件を変更してください。</div>

    <div class="section-head" id="store-list">
      <h2>STORE LIST</h2>
      <p>店舗別の簡易一覧</p>
    </div>

    <div class="simple-store-list" id="storeList">
      {stores_html}
    </div>

    <div class="section-head" id="support-links">
      <h2>SUPPORT LINKS</h2>
      <p>公式Web買取表・相場確認</p>
    </div>

    <div class="support-groups">
      {support_html}
    </div>
  </main>
</div>

<div class="nav-overlay" id="navOverlay" onclick="closeMenu(event)">
  <nav class="nav-panel" aria-label="メニュー" onclick="event.stopPropagation()">
    <div class="nav-head">
      <div class="nav-title">CARDRADAR MENU</div>
      <button class="nav-close" type="button" onclick="closeMenu()" aria-label="閉じる">×</button>
    </div>
    <div class="nav-links">
      <a href="index.html">トップ</a>
      <a href="osaka-nihonbashi.html">大阪・日本橋</a>
      <a href="osaka-nihonbashi.html#store-list" onclick="closeMenu()">店舗一覧</a>
      <a href="osaka-nihonbashi.html#support-links" onclick="closeMenu()">公式Web買取表</a>
      <a href="osaka-nihonbashi.html#support-links" onclick="closeMenu()">相場確認</a>
      <a href="#">掲載について</a>
    </div>
  </nav>
</div>

<div class="modal" id="timelineMediaModal">
  <div class="modal-inner">
    <button class="modal-close" onclick="closeTimelineMedia()">閉じる</button>
    <img class="modal-image" id="timelineModalImage" src="" alt="買取表画像">
    <div class="modal-nav">
      <button type="button" onclick="showTimelineImage(-1)">前へ</button>
      <span class="modal-counter" id="timelineModalCounter">画像 1 / 1</span>
      <button type="button" onclick="showTimelineImage(1)">次へ</button>
    </div>
    <div class="modal-summary" id="timelineModalSummary"></div>
    <div class="modal-actions">
      <a id="timelineModalTweetLink" href="#" target="_blank" rel="noopener noreferrer">Xで開く</a>
    </div>
  </div>
</div>

<script>
const selectedTypes = new Set();
const selectedBrands = new Set();
const TIMELINE_MEDIA = {media_json};
let currentSort = "new";
let currentView = "timeline";
let currentMediaItem = null;
let currentMediaIndex = 0;

function openMenu() {{
  document.getElementById("navOverlay").classList.add("open");
}}

function closeMenu(event) {{
  if (event && event.target !== document.getElementById("navOverlay")) return;
  document.getElementById("navOverlay").classList.remove("open");
}}

function toggleFilters() {{
  const searchArea = document.getElementById("searchArea");
  const brandPanel = document.getElementById("brandPanel");
  const isOpen = searchArea.classList.toggle("filters-open");
  if (brandPanel) brandPanel.setAttribute("aria-hidden", isOpen ? "false" : "true");
}}

function toggleStorePanel() {{
  const searchArea = document.getElementById("searchArea");
  const storePanel = document.getElementById("storePanel");
  const isOpen = searchArea.classList.toggle("stores-open");
  if (storePanel) storePanel.setAttribute("aria-hidden", isOpen ? "false" : "true");
}}

function renderTimelineMedia() {{
  if (!currentMediaItem) return;
  const images = currentMediaItem.image_urls || [];
  const image = images[currentMediaIndex];

  document.getElementById("timelineModalImage").src = image || "";
  document.getElementById("timelineModalCounter").textContent = `画像 ${{currentMediaIndex + 1}} / ${{Math.max(images.length, 1)}}`;
  document.getElementById("timelineModalSummary").textContent = `${{currentMediaItem.shop_name}} / ${{currentMediaItem.type_label}} / 確認：${{currentMediaItem.checked_at}}${{currentMediaItem.summary ? " / " + currentMediaItem.summary : ""}}`;
  document.getElementById("timelineModalTweetLink").href = currentMediaItem.tweet_url;
}}

function openTimelineMedia(id, startIndex = 0) {{
  currentMediaItem = TIMELINE_MEDIA[id];
  if (!currentMediaItem) return;
  const count = (currentMediaItem.image_urls || []).length;
  currentMediaIndex = count ? Math.min(Math.max(Number(startIndex) || 0, 0), count - 1) : 0;
  renderTimelineMedia();
  document.getElementById("timelineMediaModal").classList.add("open");
}}

function showTimelineImage(step) {{
  if (!currentMediaItem) return;
  const count = (currentMediaItem.image_urls || []).length;
  if (!count) return;
  currentMediaIndex = (currentMediaIndex + step + count) % count;
  renderTimelineMedia();
}}

function closeTimelineMedia() {{
  document.getElementById("timelineMediaModal").classList.remove("open");
}}

function syncTypeButtons() {{
  document.querySelectorAll(".type-row .filter-chip").forEach(btn => {{
    const type = btn.dataset.type;
    btn.classList.toggle("active", selectedTypes.size === 0 ? type === "all" : selectedTypes.has(type));
  }});
}}

function toggleType(type, button) {{
  if (type === "all") {{
    selectedTypes.clear();
  }} else if (selectedTypes.has(type)) {{
    selectedTypes.delete(type);
  }} else {{
    selectedTypes.add(type);
  }}

  syncTypeButtons();
  applyFilters();
}}

function toggleBrand(brand, button) {{
  if (selectedBrands.has(brand)) {{ selectedBrands.delete(brand); button.classList.remove("active"); }}
  else {{ selectedBrands.add(brand); button.classList.add("active"); }}
  applyFilters();
}}

function resetFilters() {{
  selectedTypes.clear();
  selectedBrands.clear();
  document.querySelectorAll(".search-input").forEach(input => input.value = "");
  document.querySelectorAll(".filter-chip").forEach(btn => btn.classList.remove("active"));
  syncTypeButtons();
  applyFilters();
}}

function setSort(sort) {{
  currentSort = sort;
  sortTimeline();
  updateResultCount();
}}

function sortTimeline() {{
  const list = document.getElementById("timelineList");
  if (!list) return;
  const posts = Array.from(list.querySelectorAll(".timeline-post"));
  const priority = {{ box: "x_post_box", fixed: "x_post_fixed", psa: "x_post_psa", single: "x_post_single" }};
  posts.sort((a, b) => {{
    if (currentSort === "store") return a.dataset.store.localeCompare(b.dataset.store, "ja") || Number(b.dataset.status) - Number(a.dataset.status);
    if (priority[currentSort]) {{
      const aHit = a.dataset.types === priority[currentSort] ? 0 : 1;
      const bHit = b.dataset.types === priority[currentSort] ? 0 : 1;
      return aHit - bHit || Number(b.dataset.status) - Number(a.dataset.status);
    }}
    return Number(b.dataset.status) - Number(a.dataset.status);
  }});
  posts.forEach(post => list.appendChild(post));
}}

function matchesItem(item, search) {{
  const typeList = item.dataset.types.split(" ");
  const brand = item.dataset.brand;
  const searchText = item.dataset.search.toLowerCase();
  const typeOk = selectedTypes.size === 0 || typeList.some(t => selectedTypes.has(t));
  const brandOk = selectedBrands.size === 0 || selectedBrands.has(brand);
  const searchOk = !search || searchText.includes(search);
  return typeOk && brandOk && searchOk;
}}

function isVisibleResultCard(card) {{
  if (!card) return false;
  if (card.classList.contains("hidden")) return false;
  if (card.closest(".view-panel.hidden")) return false;
  if (card.closest(".store-group.hidden")) return false;
  return !!(card.offsetWidth || card.offsetHeight || card.getClientRects().length);
}}

function getVisibleTimelineCards() {{
  const list = document.getElementById("timelineList");
  if (!list) return [];
  return Array.from(list.querySelectorAll(":scope > .timeline-post")).filter(card => {{
    if (card.classList.contains("hidden")) return false;
    return isVisibleResultCard(card);
  }});
}}

function getVisibleStorePostCards() {{
  const list = document.getElementById("storeGroupList");
  if (!list) return [];
  return Array.from(list.querySelectorAll(".store-post-card")).filter(card => {{
    if (card.classList.contains("hidden")) return false;
    const group = card.closest(".store-group");
    if (group && group.classList.contains("hidden")) return false;
    return isVisibleResultCard(card);
  }});
}}

function getVisibleStoreGroups() {{
  const list = document.getElementById("storeGroupList");
  if (!list) return [];
  return Array.from(list.querySelectorAll(":scope > .store-group")).filter(group => {{
    if (group.classList.contains("hidden")) return false;
    if (group.closest(".view-panel.hidden")) return false;
    return !!(group.offsetWidth || group.offsetHeight || group.getClientRects().length);
  }});
}}

function getVisibleActiveCards() {{
  return currentView === "store" ? getVisibleStoreGroups() : getVisibleTimelineCards();
}}

function updateNoResult(count) {{
  const noResult = document.getElementById("noResult");
  if (!noResult) return;
  const visibleCount = typeof count === "number" ? count : getVisibleActiveCards().length;
  const shouldShow = visibleCount === 0;
  noResult.classList.toggle("hidden", !shouldShow);
  noResult.hidden = !shouldShow;
  noResult.style.display = shouldShow ? "" : "none";
  noResult.setAttribute("aria-hidden", shouldShow ? "false" : "true");
}}

function updateResultCount() {{
  const count = getVisibleActiveCards().length;
  document.querySelectorAll(".result-count").forEach(el => el.textContent = count);
  updateNoResult(count);
}}

function applyFilters() {{
  const search = document.getElementById("searchInput").value.trim().toLowerCase();
  document.querySelectorAll(".timeline-post").forEach(post => post.classList.toggle("hidden", !matchesItem(post, search)));
  document.querySelectorAll(".simple-store-card").forEach(store => store.classList.toggle("hidden", !matchesItem(store, search)));
  document.querySelectorAll(".store-group").forEach(group => {{
    let visibleChildren = 0;
    group.querySelectorAll(".store-post-card").forEach(card => {{
      const cardMatches = matchesItem(card, search);
      card.classList.toggle("hidden", !cardMatches);
      if (cardMatches) visibleChildren += 1;
    }});
    group.classList.toggle("hidden", visibleChildren === 0);
  }});
  sortTimeline();
  updateResultCount();
}}

function setViewMode(mode) {{
  currentView = mode === "store" ? "store" : "timeline";
  document.getElementById("timelineView").classList.toggle("hidden", currentView !== "timeline");
  document.getElementById("storeView").classList.toggle("hidden", currentView !== "store");
  document.getElementById("timelineViewButton").classList.toggle("active", currentView === "timeline");
  document.getElementById("storeViewButton").classList.toggle("active", currentView === "store");
  updateResultCount();
}}

document.addEventListener("keydown", event => {{
  if (event.key === "Escape") closeMenu();
}});

function syncSearchInputs(source) {{
  document.querySelectorAll(".search-input").forEach(input => {{
    if (input !== source) input.value = source.value;
  }});
}}

document.addEventListener("DOMContentLoaded", () => {{
  const searchArea = document.getElementById("searchArea");
  const storePanel = document.getElementById("storePanel");
  const brandPanel = document.getElementById("brandPanel");
  if (searchArea) searchArea.classList.remove("stores-open");
  if (searchArea) searchArea.classList.remove("filters-open");
  if (storePanel) storePanel.setAttribute("aria-hidden", "true");
  if (brandPanel) brandPanel.setAttribute("aria-hidden", "true");
  document.getElementById("timelineViewButton").addEventListener("click", () => setViewMode("timeline"));
  document.getElementById("storeViewButton").addEventListener("click", () => setViewMode("store"));
  document.querySelectorAll(".search-input").forEach(input => {{
    const handleSearchInput = () => {{
      syncSearchInputs(input);
      applyFilters();
    }};
    input.addEventListener("input", handleSearchInput);
    input.addEventListener("search", handleSearchInput);
    input.addEventListener("change", handleSearchInput);
    input.addEventListener("keyup", handleSearchInput);
  }});
  document.getElementById("sortSelect").addEventListener("change", event => setSort(event.target.value));
  const compactSearchBar = document.getElementById("compactSearchBar");
  let lastScrollY = window.scrollY;
  const updateCompactSearchBar = () => {{
    const currentY = window.scrollY;
    const isNearTop = currentY < 160;
    const isScrollingUp = currentY < lastScrollY;
    const isFocused = compactSearchBar.contains(document.activeElement);
    const shouldShow = !isNearTop && (isScrollingUp || isFocused);
    compactSearchBar.classList.toggle("search-visible", shouldShow);
    lastScrollY = currentY;
  }};
  window.addEventListener("scroll", updateCompactSearchBar, {{ passive: true }});
  compactSearchBar.addEventListener("focusin", updateCompactSearchBar);
  compactSearchBar.addEventListener("focusout", () => setTimeout(updateCompactSearchBar, 0));
  updateCompactSearchBar();
  syncTypeButtons();
  sortTimeline();
  applyFilters();
  setViewMode("timeline");
  requestAnimationFrame(updateResultCount);
}});
</script>
"""
    return html_shell("CardRadar｜大阪日本橋のポケカ買取タイムライン", content)


# =========================
# ページ生成：店舗ページ
# =========================

def build_store_page(shop, posts_by_source, updated_at):
    sources = get_sources_by_shop(shop["shop_slug"])
    posts = get_posts_for_shop(posts_by_source, shop["shop_slug"])

    media_items = {}
    sections_html = ""

    for display_type in ["x_post_psa", "x_post_fixed", "x_post_box", "x_post_single"]:
        source_posts = [post for post in posts if post.get("display_type") == display_type]
        if not source_posts:
            continue

        meta = TYPE_META[display_type]

        images_html = ""

        media_index = 0

        for post in source_posts:
            image_urls = post.get("image_urls", [])

            for image_url in image_urls:
                media_id = f'{post.get("source_id", "post")}_{post.get("status_id", 0)}_{media_index}'
                media_index += 1

                media_items[media_id] = {
                    "image_url": image_url,
                    "tweet_url": post["tweet_url"],
                    "summary": post.get("summary", ""),
                    "type_label": post.get("display_type_label") or short_type_label(meta["label"]),
                }

                images_html += f"""
<div class="image-card" onclick="openMedia('{h(media_id)}')">
  <img src="{h(image_url)}" alt="{h(shop["shop_name"])}の買取表画像" loading="lazy">
  <div class="image-info">
    <small>{h(post.get("display_type_label") or short_type_label(meta["label"]))} / 確認 {h(format_update_label(post.get("posted_at") or post.get("collected_at", updated_at)))} / 画像{len(image_urls)}枚</small>
  </div>
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

def load_data_items():
    data_path = Path("data.json")
    if not data_path.exists():
        return []
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data_items(items):
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(dedupe_data_items(items), f, ensure_ascii=False, indent=2)


def posts_by_source_from_data(all_data):
    posts_by_source = {source["id"]: [] for source in SOURCES}
    for item in all_data:
        source_id = item.get("source_id") or item.get("id")
        source = get_source(source_id) if source_id else None
        normalized = normalize_post(item, source)
        if not normalized.get("tweet_url") or not source_id:
            continue
        posts_by_source.setdefault(source_id, []).append(normalized)
    for posts in posts_by_source.values():
        posts.sort(key=sort_post_key, reverse=True)
    return posts_by_source


def replace_source_items(all_data, source_id, new_items):
    kept = [item for item in all_data if (item.get("source_id") or item.get("id")) != source_id]
    return dedupe_data_items(kept + new_items)


def select_sources(area_id=None, source_id=None, max_sources=None):
    selected = SOURCES
    if area_id:
        selected = [source for source in selected if source.get("area_id") == area_id]
    if source_id:
        selected = [source for source in selected if source.get("id") == source_id]
    if max_sources is not None:
        selected = selected[:max_sources]
    return selected


def collect_posts(sources_to_fetch=None, quick=False, previous_data=None):
    previous_data = previous_data if previous_data is not None else load_data_items()
    posts_by_source = posts_by_source_from_data(previous_data)
    all_data = list(previous_data)
    updated_at = datetime.now().strftime("%Y/%m/%d %H:%M")
    target_sources = sources_to_fetch or SOURCES

    initial_wait = 4 if quick else 10
    scroll_count = 2 if quick else 6
    scroll_wait = 1 if quick else 3
    check_limit = 25 if quick else CHECK_POSTS_PER_SOURCE

    print(f"取得対象source数: {len(target_sources)}")
    if quick:
        print("quickモード: wait短縮 / scroll短縮 / article確認数削減")

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

        for source in target_sources:
            print("")
            print("==============================")
            print(f"{source['id']} / {source['shop_name']} / {TYPE_META[source['source_type']]['label']}")
            print("==============================")

            if not is_x_source(source):
                data_item = normalize_post({
                    **source,
                    "source_id": source["id"],
                    "display_type": source["source_type"],
                    "display_type_label": short_type_label(TYPE_META[source["source_type"]]["label"]),
                    "buy_type_label": TYPE_META[source["source_type"]]["label"],
                    "collected_at": updated_at,
                }, source)
                all_data = replace_source_items(all_data, source["id"], [data_item])
                save_data_items(all_data)
                print("リンク情報として保存")
                continue

            candidates = []
            seen_urls = set()

            try:
                page.goto(source["url"], wait_until="domcontentloaded", timeout=60000)
                time.sleep(initial_wait)

                page.wait_for_selector("article", timeout=30000)

                for _ in range(scroll_count):
                    page.mouse.wheel(0, 1400)
                    time.sleep(scroll_wait)

                tweets = page.locator("article")
                count = tweets.count()

                print("検出article数:", count)

                for i in range(min(count, check_limit)):
                    tweet = tweets.nth(i)

                    text = tweet.inner_text()
                    url = get_status_url(tweet)

                    if not url:
                        continue

                    if url in seen_urls:
                        continue

                    if not is_target_post(text, source["source_type"]):
                        print(f"[除外] {source['shop_name']} source={source['source_type']} display=- date=- reason=not target")
                        continue

                    image_urls = get_image_urls(tweet)

                    if not image_urls:
                        print(f"[除外] {source['shop_name']} source={source['source_type']} display=- date=- reason=no image")
                        continue

                    seen_urls.add(url)
                    posted_at = get_posted_at(tweet)
                    posted_date_jst = posted_date_from_values(posted_at, updated_at)
                    display_type, reason = classify_display_type(text, source["source_type"])

                    post = normalize_post({
                        "source_id": source["id"],
                        "source_type": source["source_type"],
                        "display_type": display_type,
                        "display_type_label": display_type_label(display_type),
                        "buy_type_label": TYPE_META[source["source_type"]]["label"],
                        "shop_name": source["shop_name"],
                        "shop_slug": source["shop_slug"],
                        "brand": source["brand"],
                        "brand_id": source["brand_id"],
                        "area": source["area"],
                        "area_id": source["area_id"],
                        "tweet_url": url,
                        "status_id": get_status_id(url),
                        "full_text": text,
                        "summary": clean_tweet_text(text),
                        "image_urls": image_urls,
                        "image_count": len(image_urls),
                        "posted_at": posted_at,
                        "posted_date_jst": posted_date_jst,
                        "collected_at": updated_at,
                        "classify_reason": reason,
                    }, source)

                    candidates.append(post)

                print(f"[候補] {source['shop_name']} {source['source_type']} candidates={len(candidates)}")
                posts = select_latest_posts(candidates)

                posts_by_source[source["id"]] = posts
                all_data = replace_source_items(all_data, source["id"], posts)
                save_data_items(all_data)

                latest_date = posts[0].get("posted_date_jst", "-") if posts else "-"
                print(f"[最新日] {latest_date}")
                print(f"[採用] {len(posts)}件")
                for post in posts:
                    print(f"[分類] {post['shop_name']} source={post['source_type']} display={post['display_type']} date={post.get('posted_date_jst') or '-'} reason={post.get('classify_reason') or '-'}")

            except Exception as e:
                print(f"[失敗] {source['id']} reason={e}")
                print("前回data.jsonのデータを残します")

        browser.close()

    return posts_by_source_from_data(all_data), dedupe_data_items(all_data), updated_at


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


def rebuild_html_from_data():
    data_path = Path("data.json")

    if not data_path.exists():
        print("data.json がありません。先に python test.py で取得してください。")
        return 1

    with open(data_path, "r", encoding="utf-8") as f:
        all_data = json.load(f)

    posts_by_source = {}
    updated_at = datetime.now().strftime("%Y/%m/%d %H:%M")

    if all_data:
        updated_at = all_data[0].get("collected_at", updated_at)

    for source in SOURCES:
        posts_by_source[source["id"]] = []

    for item in all_data:
        source_id = item.get("source_id") or item.get("id")
        source = get_source(source_id) if source_id else None
        normalized = normalize_post(item, source)
        if not normalized.get("tweet_url") or not source_id:
            continue
        posts_by_source.setdefault(source_id, []).append(normalized)

    for posts in posts_by_source.values():
        posts.sort(key=sort_post_key, reverse=True)

    build_all_pages(posts_by_source, updated_at)

    print("HTML再生成完了")
    print("index.html")
    print("osaka.html")
    print("osaka-nihonbashi.html")
    print("stores/*.html")
    return 0


def parse_args():
    parser = argparse.ArgumentParser(description="CardRadar data collector")
    parser.add_argument("--rebuild-html", action="store_true", help="既存data.jsonからHTMLだけ再生成する")
    parser.add_argument("--area", help="指定area_idのsourceだけ取得する")
    parser.add_argument("--source", help="指定source_idだけ取得する")
    parser.add_argument("--max-sources", type=int, help="先頭から指定数のsourceだけ取得する")
    parser.add_argument("--quick", action="store_true", help="待機とスクロールを短縮して軽量取得する")
    return parser.parse_args()


def main():
    args = parse_args()

    if args.rebuild_html:
        return rebuild_html_from_data()

    selected_sources = select_sources(args.area, args.source, args.max_sources)
    if args.source and not selected_sources:
        print(f"source_id が見つかりません: {args.source}")
        return 1
    if args.area and not selected_sources:
        print(f"area_id のsourceが見つかりません: {args.area}")
        return 1

    posts_by_source, all_data, updated_at = collect_posts(selected_sources, quick=args.quick)
    all_data = dedupe_data_items(all_data)
    save_data_items(all_data)

    build_all_pages(posts_by_source, updated_at)

    print("")
    print("================================")
    print("生成完了")
    print("index.html")
    print("osaka.html")
    print("osaka-nihonbashi.html")
    print("stores/*.html")
    print("data.json")
    print("================================")

    if len(sys.argv) == 1:
        input("Enterで終了")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())




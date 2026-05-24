from playwright.sync_api import sync_playwright
import time
import re
from datetime import datetime
import html as html_lib
import json


# userdataをGitHub管理フォルダの外に置いている場合
USER_DATA_DIR = "../userdata"

# もし動かない・ログインが外れる場合はこちらに変更
# USER_DATA_DIR = "userdata"


MAX_TWEETS_PER_SHOP = 3
CHECK_TWEETS_PER_SHOP = 30


SOURCES = [
    # =========================
    # 大阪・日本橋・なんば / ドラゴンスター
    # =========================
    {
        "source_type": "x_post",
        "name": "ドラスタ オタロード中央",
        "short": "オタ中",
        "id": "otachu",
        "area": "大阪・日本橋・なんば",
        "area_id": "osaka-nihonbashi",
        "prefecture": "大阪",
        "brand": "ドラゴンスター",
        "brand_id": "dragonstar",
        "game": "ポケカ",
        "tag": "ポケカ買取",
        "icon": "D",
        "color": "#2563eb",
        "description": "ドラゴンスター オタロード中央店のポケカ買取表・高価買取情報を確認できます。",
        "url": "https://x.com/search?q=from%3Ads_otaroad_chuo%20ポケカ%20買取%20filter%3Aimages&src=typed_query&f=live",
    },
    {
        "source_type": "x_post",
        "name": "ドラスタ 日本橋本店",
        "short": "本店",
        "id": "honten",
        "area": "大阪・日本橋・なんば",
        "area_id": "osaka-nihonbashi",
        "prefecture": "大阪",
        "brand": "ドラゴンスター",
        "brand_id": "dragonstar",
        "game": "ポケカ",
        "tag": "ポケカ買取",
        "icon": "DH",
        "color": "#1d4ed8",
        "description": "ドラゴンスター 日本橋本店のポケカ買取情報を確認できます。",
        "url": "https://x.com/search?q=from%3Ads_nipponbashi%20ポケカ%20買取%20filter%3Aimages&src=typed_query&f=live",
    },
    {
        "source_type": "x_post",
        "name": "ドラスタ 日本橋2号店",
        "short": "ドラ2",
        "id": "dora2",
        "area": "大阪・日本橋・なんば",
        "area_id": "osaka-nihonbashi",
        "prefecture": "大阪",
        "brand": "ドラゴンスター",
        "brand_id": "dragonstar",
        "game": "ポケカ",
        "tag": "ポケカ買取",
        "icon": "D2",
        "color": "#7c3aed",
        "description": "ドラゴンスター 日本橋2号店のポケカ買取表・WANTED情報を確認できます。",
        "url": "https://x.com/search?q=from%3Ads_nipponbashi2%20ポケカ%20買取%20filter%3Aimages&src=typed_query&f=live",
    },
    {
        "source_type": "x_post",
        "name": "ドラスタ 日本橋3号店",
        "short": "ドラ3",
        "id": "dora3",
        "area": "大阪・日本橋・なんば",
        "area_id": "osaka-nihonbashi",
        "prefecture": "大阪",
        "brand": "ドラゴンスター",
        "brand_id": "dragonstar",
        "game": "ポケカ",
        "tag": "ポケカ買取",
        "icon": "D3",
        "color": "#dc2626",
        "description": "ドラゴンスター 日本橋3号店のポケカ高価買取情報を確認できます。",
        "url": "https://x.com/search?q=from%3Ads_nipponbashi3%20ポケカ%20買取%20filter%3Aimages&src=typed_query&f=live",
    },
    {
        "source_type": "x_post",
        "name": "ドラスタ なんさん通り店",
        "short": "なんさん",
        "id": "nansan",
        "area": "大阪・日本橋・なんば",
        "area_id": "osaka-nihonbashi",
        "prefecture": "大阪",
        "brand": "ドラゴンスター",
        "brand_id": "dragonstar",
        "game": "ポケカ",
        "tag": "ポケカ買取",
        "icon": "DN",
        "color": "#0891b2",
        "description": "ドラゴンスター なんさん通り店のポケカ買取情報を確認できます。",
        "url": "https://x.com/search?q=from%3Ads_namba_nansan%20ポケカ%20買取%20filter%3Aimages&src=typed_query&f=live",
    },

    # =========================
    # 大阪・日本橋・なんば / 晴れる屋2
    # =========================
    {
        "source_type": "x_post",
        "name": "晴れる屋2なんば",
        "short": "晴れる屋2",
        "id": "hareruya2",
        "area": "大阪・日本橋・なんば",
        "area_id": "osaka-nihonbashi",
        "prefecture": "大阪",
        "brand": "晴れる屋2",
        "brand_id": "hareruya2",
        "game": "ポケカ",
        "tag": "ポケカ買取",
        "icon": "H",
        "color": "#059669",
        "description": "晴れる屋2なんば店のポケカ買取表・買取情報を確認できます。",
        "url": "https://x.com/search?q=from%3Ahareruya2namba%20ポケカ%20買取%20filter%3Aimages&src=typed_query&f=live",
    },

    # =========================
    # 大阪・日本橋・なんば / カードラボ
    # =========================
    {
        "source_type": "x_post",
        "name": "カードラボなんば店",
        "short": "ラボなんば",
        "id": "labo-namba",
        "area": "大阪・日本橋・なんば",
        "area_id": "osaka-nihonbashi",
        "prefecture": "大阪",
        "brand": "カードラボ",
        "brand_id": "cardlabo",
        "game": "ポケカ",
        "tag": "ポケカ買取",
        "icon": "L",
        "color": "#f59e0b",
        "description": "カードラボなんば店のポケカ買取情報を確認できます。",
        "url": "https://x.com/search?q=from%3Anamba_clabo%20ポケカ%20買取%20filter%3Aimages&src=typed_query&f=live",
    },
    {
        "source_type": "x_post",
        "name": "カードラボ大阪日本橋店",
        "short": "ラボ日本橋",
        "id": "labo-nihonbashi",
        "area": "大阪・日本橋・なんば",
        "area_id": "osaka-nihonbashi",
        "prefecture": "大阪",
        "brand": "カードラボ",
        "brand_id": "cardlabo",
        "game": "ポケカ",
        "tag": "ポケカ買取",
        "icon": "LN",
        "color": "#ec4899",
        "description": "カードラボ大阪日本橋店のポケカ買取情報を確認できます。",
        "url": "https://x.com/search?q=from%3Anipponbashi_lab%20ポケカ%20買取%20filter%3Aimages&src=typed_query&f=live",
    },
    {
        "source_type": "x_post",
        "name": "カードラボ販売買取センターNAMBA",
        "short": "ラボ買取",
        "id": "labo-kaitori",
        "area": "大阪・日本橋・なんば",
        "area_id": "osaka-nihonbashi",
        "prefecture": "大阪",
        "brand": "カードラボ",
        "brand_id": "cardlabo",
        "game": "ポケカ",
        "tag": "ポケカ買取",
        "icon": "LC",
        "color": "#14b8a6",
        "description": "カードラボ販売買取センターNAMBAのポケカ買取情報を確認できます。",
        "url": "https://x.com/search?q=from%3Ananba2_labo%20ポケカ%20買取%20filter%3Aimages&src=typed_query&f=live",
    },

    # =========================
    # 大阪・日本橋・なんば / GIRAFULL
    # =========================
    {
        "source_type": "x_post",
        "name": "GIRAFULLなんば店",
        "short": "ジラなんば",
        "id": "gira-namba",
        "area": "大阪・日本橋・なんば",
        "area_id": "osaka-nihonbashi",
        "prefecture": "大阪",
        "brand": "GIRAFULL",
        "brand_id": "girafull",
        "game": "ポケカ",
        "tag": "ポケカ買取",
        "icon": "G",
        "color": "#ea580c",
        "description": "GIRAFULLなんば店のポケカ買取情報を確認できます。",
        "url": "https://x.com/search?q=from%3AGIRAFULL_Namba%20ポケカ%20買取%20filter%3Aimages&src=typed_query&f=live",
    },
    {
        "source_type": "x_post",
        "name": "GIRAFULL大阪日本橋店",
        "short": "ジラ日本橋",
        "id": "gira-nihonbashi",
        "area": "大阪・日本橋・なんば",
        "area_id": "osaka-nihonbashi",
        "prefecture": "大阪",
        "brand": "GIRAFULL",
        "brand_id": "girafull",
        "game": "ポケカ",
        "tag": "ポケカ買取",
        "icon": "GN",
        "color": "#f97316",
        "description": "GIRAFULL大阪日本橋店のポケカ買取情報を確認できます。",
        "url": "https://x.com/search?q=from%3Agirafull_o_n%20ポケカ%20買取%20filter%3Aimages&src=typed_query&f=live",
    },
    {
        "source_type": "x_post",
        "name": "GIRAFULLオタロード店",
        "short": "ジラオタ",
        "id": "gira-otaroad",
        "area": "大阪・日本橋・なんば",
        "area_id": "osaka-nihonbashi",
        "prefecture": "大阪",
        "brand": "GIRAFULL",
        "brand_id": "girafull",
        "game": "ポケカ",
        "tag": "ポケカ買取",
        "icon": "GO",
        "color": "#fb923c",
        "description": "GIRAFULLオタロード店のポケカ買取情報を確認できます。",
        "url": "https://x.com/search?q=from%3AGIRAFULLOTARODO%20ポケカ%20買取%20filter%3Aimages&src=typed_query&f=live",
    },

    # =========================
    # オンライン買取表
    # =========================
    {
        "source_type": "online_price_list",
        "name": "Clove Base",
        "short": "Clove",
        "id": "clove-base",
        "area": "オンライン",
        "area_id": "online",
        "prefecture": "オンライン",
        "brand": "Clove",
        "brand_id": "clove",
        "game": "ポケカ",
        "tag": "オンライン買取表",
        "icon": "C",
        "color": "#6366f1",
        "official_url": "https://base.clove.jp/prices/pokemon",
        "description": "ポケモンカードのオンライン買取価格表。カード名や買取価格を確認できます。",
    },
    {
        "source_type": "online_price_list",
        "name": "フルアヘッド",
        "short": "フルアヘッド",
        "id": "fullahead",
        "area": "オンライン",
        "area_id": "online",
        "prefecture": "オンライン",
        "brand": "フルアヘッド",
        "brand_id": "fullahead",
        "game": "ポケカ",
        "tag": "オンライン買取表",
        "icon": "F",
        "color": "#16a34a",
        "official_url": "https://fullahead-buy.com/",
        "description": "ポケモンカードゲームを含む各種TCGの高価買取リストを確認できます。",
    },
]


def is_pokemon_buy_post(text):
    pokemon_words = [
        "ポケカ",
        "ポケモンカード",
        "ポケモンカードゲーム",
        "ﾎﾟｹﾓﾝｶｰﾄﾞ",
        "pokemon",
        "Pokemon",
        "POKEMON",
    ]

    buy_words = [
        "買取",
        "高価買取",
        "買取表",
        "買取表ダ",
        "WANTED",
        "募集",
        "取扱強化",
        "お持ち込み",
        "超本気買取",
        "買取情報",
        "更新Ver",
        "更新ver",
    ]

    ng_words = [
        "大会情報",
        "大会",
        "優勝",
        "ショップバトル",
        "プレリリース",
        "ワンピース",
        "ワンピ",
        "バトスピ",
        "デジカ",
        "ガンダム",
        "MTG",
        "遊戯王",
        "デュエマ",
        "ヴァイス",
    ]

    if any(word in text for word in ng_words):
        return False

    has_pokemon = any(word in text for word in pokemon_words)
    has_buy = any(word in text for word in buy_words)

    return has_pokemon and has_buy


def clean_tweet_text(text):
    lines = text.splitlines()
    cleaned = []

    skip_words = [
        "さらに表示",
        "返信先:",
        "さん",
    ]

    for line in lines:
        line = line.strip()

        if not line:
            continue

        if line.startswith("@"):
            continue

        if line == "·":
            continue

        if any(word in line for word in skip_words):
            continue

        if re.fullmatch(r"[0-9,\.万]+", line):
            continue

        if "ドラゴンスター" in line and len(line) < 25:
            continue

        if "晴れる屋2" in line and len(line) < 30:
            continue

        if "カードラボ" in line and len(line) < 30:
            continue

        if "GIRAFULL" in line and len(line) < 30:
            continue

        cleaned.append(line)

    summary = " ".join(cleaned)

    if len(summary) > 200:
        summary = summary[:200] + "..."

    if not summary:
        summary = "画像付きのポケカ買取投稿です。"

    return summary


def get_status_url(tweet):
    links = tweet.locator("a")
    link_count = links.count()

    for j in range(link_count):
        href = links.nth(j).get_attribute("href")

        if not href:
            continue

        if "/status/" in href and "/photo/" not in href and "/analytics" not in href:
            full_url = "https://x.com" + href if href.startswith("/") else href
            return full_url

    return None


def get_status_id(url):
    match = re.search(r"/status/(\d+)", url)

    if match:
        return int(match.group(1))

    return 0


def get_image_urls(tweet):
    image_urls = []
    images = tweet.locator("img")
    image_count = images.count()

    for i in range(image_count):
        src = images.nth(i).get_attribute("src")

        if not src:
            continue

        if "pbs.twimg.com/media" in src:
            src = src.replace("name=small", "name=large")
            src = src.replace("name=medium", "name=large")

            if src not in image_urls:
                image_urls.append(src)

    return image_urls


def get_unique_areas():
    areas = []

    for source in SOURCES:
        area_id = source["area_id"]

        if not any(area["area_id"] == area_id for area in areas):
            areas.append({
                "area": source["area"],
                "area_id": area_id,
            })

    return areas


def get_sources_by_area(area_id):
    return [source for source in SOURCES if source["area_id"] == area_id]


def get_brands_by_area(area_sources):
    brands = []

    for source in area_sources:
        brand_id = source["brand_id"]

        if not any(brand["brand_id"] == brand_id for brand in brands):
            brands.append({
                "brand": source["brand"],
                "brand_id": brand_id,
            })

    return brands


def build_html_start(updated_at):
    html_doc = """
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>CardRadar｜大阪日本橋・なんばのポケカ買取表まとめ</title>
<meta name="description" content="CardRadarは、大阪・日本橋・なんば周辺のカードショップがXに投稿しているポケカ買取表を店舗別にまとめて確認できるサイトです。ドラゴンスター、晴れる屋2、カードラボ、GIRAFULL、オンライン買取表も掲載。">

<style>
* {
    box-sizing: border-box;
}

html {
    scroll-behavior: smooth;
}

body {
    margin: 0;
    font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
    background: #0f172a;
    color: #111827;
}

header {
    background:
        radial-gradient(circle at top left, rgba(59,130,246,0.38), transparent 34%),
        linear-gradient(135deg, #020617, #111827 55%, #1e293b);
    color: white;
    padding: 42px 20px 32px;
}

.header-inner {
    max-width: 1120px;
    margin: 0 auto;
}

.logo-row {
    display: flex;
    align-items: center;
    gap: 12px;
}

.site-icon {
    width: 48px;
    height: 48px;
    border-radius: 16px;
    background: #2563eb;
    display: grid;
    place-items: center;
    font-weight: 900;
    box-shadow: 0 10px 24px rgba(37,99,235,0.35);
}

.logo {
    font-size: 36px;
    font-weight: 850;
    margin: 0;
}

.lead {
    margin: 12px 0 0;
    color: #cbd5e1;
    font-size: 15px;
    line-height: 1.8;
    max-width: 880px;
}

.meta {
    margin-top: 16px;
    display: inline-block;
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.16);
    padding: 7px 12px;
    border-radius: 999px;
    font-size: 13px;
    color: #e5e7eb;
}

nav {
    max-width: 1120px;
    margin: -18px auto 0;
    padding: 0 14px;
    position: sticky;
    top: 0;
    z-index: 10;
}

.nav-inner {
    background: rgba(255,255,255,0.96);
    backdrop-filter: blur(10px);
    border-radius: 16px;
    padding: 10px;
    display: flex;
    gap: 8px;
    overflow-x: auto;
    box-shadow: 0 10px 26px rgba(0,0,0,0.18);
}

.nav-inner a {
    color: #111827;
    text-decoration: none;
    background: #f3f4f6;
    padding: 9px 13px;
    border-radius: 999px;
    font-size: 13px;
    white-space: nowrap;
    border: 1px solid #e5e7eb;
    font-weight: 700;
}

.nav-inner a:hover {
    background: #dbeafe;
    color: #1d4ed8;
}

main {
    max-width: 1120px;
    margin: 0 auto;
    padding: 28px 14px 44px;
}

.summary {
    background: white;
    border-radius: 22px;
    padding: 22px;
    margin-bottom: 26px;
    box-shadow: 0 10px 28px rgba(0,0,0,0.16);
}

.summary h2 {
    margin: 0 0 8px;
    font-size: 22px;
}

.summary p {
    margin: 0;
    color: #4b5563;
    font-size: 14px;
    line-height: 1.9;
}

.notice {
    margin-top: 14px;
    background: #f8fafc;
    border: 1px solid #e5e7eb;
    padding: 12px;
    border-radius: 14px;
    color: #475569;
    font-size: 13px;
    line-height: 1.7;
}

.area-section {
    margin-bottom: 40px;
    scroll-margin-top: 90px;
}

.area-title {
    color: white;
    margin: 34px 0 16px;
}

.area-title h2 {
    font-size: 28px;
    margin: 0;
}

.area-title p {
    color: #cbd5e1;
    margin: 8px 0 0;
    font-size: 14px;
    line-height: 1.7;
}

.brand-section {
    margin-bottom: 30px;
}

.brand-title {
    color: #e5e7eb;
    font-size: 20px;
    margin: 0 0 14px;
    padding-left: 10px;
    border-left: 5px solid #60a5fa;
}

.shop {
    background: white;
    border-radius: 22px;
    padding: 18px;
    margin-bottom: 22px;
    box-shadow: 0 10px 28px rgba(0,0,0,0.18);
}

.shop-head {
    display: flex;
    justify-content: space-between;
    gap: 14px;
    align-items: center;
    border-bottom: 1px solid #e5e7eb;
    padding-bottom: 15px;
    margin-bottom: 18px;
}

.shop-title {
    display: flex;
    align-items: center;
    gap: 12px;
}

.shop-icon {
    width: 46px;
    height: 46px;
    border-radius: 16px;
    display: grid;
    place-items: center;
    color: white;
    font-weight: 900;
    flex: 0 0 auto;
}

.shop h3 {
    margin: 0;
    font-size: 21px;
}

.shop-description {
    margin: 6px 0 0;
    color: #6b7280;
    font-size: 13px;
    line-height: 1.6;
}

.badge {
    display: inline-block;
    background: #dbeafe;
    color: #1d4ed8;
    padding: 5px 11px;
    border-radius: 999px;
    font-size: 13px;
    margin-bottom: 7px;
    font-weight: 700;
}

.count {
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    color: #374151;
    border-radius: 999px;
    padding: 8px 13px;
    font-size: 13px;
    white-space: nowrap;
}

.tweet-list {
    display: grid;
    grid-template-columns: 1fr;
    gap: 26px;
    justify-items: center;
}

.post-card {
    width: 100%;
    max-width: 640px;
    background: #f8fafc;
    border: 1px solid #e5e7eb;
    border-radius: 18px;
    padding: 14px;
}

.post-summary {
    margin-bottom: 12px;
}

.post-summary-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 800;
    color: #111827;
    font-size: 14px;
    margin-bottom: 7px;
    flex-wrap: wrap;
}

.hot {
    background: #fee2e2;
    color: #b91c1c;
    padding: 3px 8px;
    border-radius: 999px;
    font-size: 12px;
}

.image-count {
    background: #dcfce7;
    color: #166534;
    padding: 3px 8px;
    border-radius: 999px;
    font-size: 12px;
}

.post-summary p {
    margin: 0;
    color: #374151;
    font-size: 14px;
    line-height: 1.7;
}

.tweet {
    width: 100%;
    max-width: 560px;
    margin: 0 auto;
}

.online-card {
    background: #f8fafc;
    border: 1px solid #e5e7eb;
    border-radius: 18px;
    padding: 16px;
}

.online-card p {
    margin: 0 0 14px;
    color: #374151;
    font-size: 14px;
    line-height: 1.8;
}

.online-button {
    display: inline-block;
    text-decoration: none;
    background: #111827;
    color: white;
    padding: 10px 14px;
    border-radius: 12px;
    font-weight: 700;
    font-size: 14px;
}

.online-button:hover {
    background: #2563eb;
}

.empty {
    color: #6b7280;
    background: #f9fafb;
    padding: 14px;
    border-radius: 12px;
}

.contact-box {
    background: #ffffff;
    border-radius: 22px;
    padding: 20px;
    margin-top: 34px;
    box-shadow: 0 10px 28px rgba(0,0,0,0.16);
}

.contact-box h2 {
    margin: 0 0 8px;
    font-size: 22px;
}

.contact-box p {
    margin: 0;
    color: #4b5563;
    font-size: 14px;
    line-height: 1.8;
}

footer {
    text-align: center;
    color: #cbd5e1;
    padding: 34px 20px;
    font-size: 13px;
}

@media (max-width: 640px) {
    header {
        padding: 30px 16px 26px;
    }

    .logo {
        font-size: 29px;
    }

    .lead {
        font-size: 14px;
    }

    nav {
        margin-top: -14px;
    }

    .shop {
        border-radius: 18px;
        padding: 14px;
    }

    .shop-head {
        display: block;
    }

    .shop-title {
        align-items: flex-start;
    }

    .count {
        display: inline-block;
        margin-top: 12px;
    }

    .shop h3 {
        font-size: 18px;
    }

    .post-card {
        padding: 12px;
    }
}
</style>
</head>

<body>

<header>
    <div class="header-inner">
        <div class="logo-row">
            <div class="site-icon">CR</div>
            <h1 class="logo">CardRadar</h1>
        </div>
        <p class="lead">
            大阪・日本橋・なんば周辺のカードショップがXに投稿しているポケカ買取表を、地域別・ブランド別・店舗別にまとめて確認できます。
            ドラゴンスター、晴れる屋2、カードラボ、GIRAFULLのX買取情報に加えて、Clove Baseやフルアヘッドなどのオンライン買取表も掲載しています。
        </p>
        <div class="meta">最終更新：__UPDATED_AT__</div>
    </div>
</header>

<nav>
    <div class="nav-inner">
"""
    html_doc = html_doc.replace("__UPDATED_AT__", updated_at)
    return html_doc


def build_html_end():
    return """
</main>

<footer>
    CardRadar - TCG買取情報まとめ
</footer>

<script async src="https://platform.twitter.com/widgets.js"></script>

</body>
</html>
"""


updated_at = datetime.now().strftime("%Y/%m/%d %H:%M")
all_posts_data = []

html_doc = build_html_start(updated_at)

for area in get_unique_areas():
    html_doc += f'<a href="#{area["area_id"]}">{area["area"]}</a>\n'

html_doc += """
    </div>
</nav>

<main>

<section class="summary">
    <h2>ポケカ買取表を地域別・店舗別にチェック</h2>
    <p>
        CardRadarは、日本橋・なんば周辺を中心に、カードショップが公開しているポケモンカードの買取表をまとめて確認できるサイトです。
        Xに投稿された画像付き買取表と、オンライン買取価格表へのリンクを分けて掲載しています。
    </p>
    <div class="notice">
        表示されるX投稿はXの埋め込み機能を利用しています。画像URLはOCR準備用としてdata.jsonに保存しますが、サイト上では画像を再配布しません。
        掲載内容は各店舗の投稿・公式ページを必ずご確認ください。
    </div>
</section>
"""


with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        user_data_dir=USER_DATA_DIR,
        headless=False
    )

    page = browser.new_page()

    for area in get_unique_areas():
        area_sources = get_sources_by_area(area["area_id"])

        html_doc += f"""
<section class="area-section" id="{area["area_id"]}">
    <div class="area-title">
        <h2>{area["area"]}</h2>
        <p>{area["area"]}のポケカ買取表・オンライン買取情報をまとめています。</p>
    </div>
"""

        brands = get_brands_by_area(area_sources)

        for brand in brands:
            brand_sources = [
                source for source in area_sources
                if source["brand_id"] == brand["brand_id"]
            ]

            html_doc += f"""
    <section class="brand-section">
        <h2 class="brand-title">{brand["brand"]}</h2>
"""

            for source in brand_sources:
                print("==============")
                print(source["name"])
                print("==============")

                if source["source_type"] == "online_price_list":
                    data_item = {
                        "source_type": source["source_type"],
                        "name": source["name"],
                        "area": source["area"],
                        "area_id": source["area_id"],
                        "brand": source["brand"],
                        "brand_id": source["brand_id"],
                        "game": source["game"],
                        "official_url": source["official_url"],
                        "description": source["description"],
                        "collected_at": updated_at,
                    }

                    all_posts_data.append(data_item)

                    safe_description = html_lib.escape(source["description"])

                    html_doc += f"""
        <article class="shop">
            <div class="shop-head">
                <div class="shop-title">
                    <div class="shop-icon" style="background:{source["color"]};">{source["icon"]}</div>
                    <div>
                        <span class="badge">{source["tag"]}</span>
                        <h3>{source["name"]}</h3>
                        <p class="shop-description">{safe_description}</p>
                    </div>
                </div>
                <div class="count">公式リンク</div>
            </div>

            <div class="online-card">
                <p>{safe_description}</p>
                <a class="online-button" href="{source["official_url"]}" target="_blank" rel="noopener noreferrer">公式買取表を見る</a>
            </div>
        </article>
"""
                    continue

                posts = []
                seen_urls = set()
                candidate_posts = []

                try:
                    page.goto(source["url"], wait_until="domcontentloaded", timeout=60000)
                    time.sleep(10)

                    # X検索結果の読み込みを増やす
                    for _ in range(3):
                        page.mouse.wheel(0, 1200)
                        time.sleep(2)

                    tweets = page.locator("article")
                    count = tweets.count()

                    print("検出article数:", count)

                    for i in range(min(count, CHECK_TWEETS_PER_SHOP)):
                        tweet = tweets.nth(i)

                        url = get_status_url(tweet)

                        if not url:
                            continue

                        if url in seen_urls:
                            continue

                        text = tweet.inner_text()

                        if not is_pokemon_buy_post(text):
                            print("除外:", url)
                            continue

                        image_urls = get_image_urls(tweet)

                        if not image_urls:
                            print("画像なし除外:", url)
                            continue

                        summary = clean_tweet_text(text)

                        seen_urls.add(url)

                        post = {
                            "source_type": source["source_type"],
                            "shop_name": source["name"],
                            "shop_id": source["id"],
                            "shop_short": source["short"],
                            "area": source["area"],
                            "area_id": source["area_id"],
                            "prefecture": source["prefecture"],
                            "brand": source["brand"],
                            "brand_id": source["brand_id"],
                            "game": source["game"],
                            "tag": source["tag"],
                            "tweet_url": url,
                            "status_id": get_status_id(url),
                            "summary": summary,
                            "image_urls": image_urls,
                            "image_count": len(image_urls),
                            "collected_at": updated_at,
                        }

                        candidate_posts.append(post)

                    candidate_posts.sort(key=lambda x: x["status_id"], reverse=True)
                    posts = candidate_posts[:MAX_TWEETS_PER_SHOP]

                    for post in posts:
                        all_posts_data.append(post)
                        print("採用:", post["tweet_url"])
                        print("画像数:", post["image_count"])

                except Exception as e:
                    print("取得エラー:", e)

                safe_description = html_lib.escape(source["description"])

                html_doc += f"""
        <article class="shop">
            <div class="shop-head">
                <div class="shop-title">
                    <div class="shop-icon" style="background:{source["color"]};">{source["icon"]}</div>
                    <div>
                        <span class="badge">{source["tag"]}</span>
                        <h3>{source["name"]}</h3>
                        <p class="shop-description">{safe_description}</p>
                    </div>
                </div>
                <div class="count">{len(posts)}件表示</div>
            </div>

            <div class="tweet-list">
"""

                if posts:
                    for post in posts:
                        safe_summary = html_lib.escape(post["summary"])

                        html_doc += f"""
                <div class="post-card">
                    <div class="post-summary">
                        <div class="post-summary-title">
                            <span class="hot">買取情報</span>
                            <span class="image-count">画像{post["image_count"]}枚</span>
                            <span>投稿内容</span>
                        </div>
                        <p>{safe_summary}</p>
                    </div>

                    <div class="tweet">
                        <blockquote class="twitter-tweet">
                            <a href="{post["tweet_url"]}"></a>
                        </blockquote>
                    </div>
                </div>
"""
                else:
                    html_doc += """
                <div class="empty">該当する投稿が見つかりませんでした。</div>
"""

                html_doc += """
            </div>
        </article>
"""

            html_doc += """
    </section>
"""

        html_doc += """
</section>
"""

    html_doc += """
<section class="contact-box">
    <h2>掲載店舗・買取表情報を募集中</h2>
    <p>
        CardRadarでは、ポケカ買取表を定期的に投稿しているカードショップや、オンライン買取表を掲載しているサービスを順次追加予定です。
        今後は地域別ページ、カード名検索、買取価格比較、更新通知にも対応していきます。
    </p>
</section>
"""

    html_doc += build_html_end()

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_doc)

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(all_posts_data, f, ensure_ascii=False, indent=2)

    print("")
    print("index.html を生成しました")
    print("data.json を生成しました")
    print("取得データ数:", len(all_posts_data))

    input("終了するにはEnter")

    browser.close()
    
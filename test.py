from playwright.sync_api import sync_playwright
import time
import re
from datetime import datetime
import html as html_lib
import json

# userdataをGitHub管理フォルダの外に置いている場合
USER_DATA_DIR = "../userdata"

# ログインが外れる・動かない場合だけこちらに変更
# USER_DATA_DIR = "userdata"

MAX_TWEETS_PER_SHOP = 3
CHECK_TWEETS_PER_SHOP = 12

SEARCHES = [
    {
        "name": "ドラスタ オタロード中央",
        "short": "オタ中",
        "id": "otachu",
        "tag": "ポケカ買取",
        "icon": "D",
        "color": "#2563eb",
        "url": "https://x.com/search?q=from%3Ads_otaroad_chuo%20ポケカ%20買取%20filter%3Aimages&src=typed_query&f=live",
    },
    {
        "name": "ドラスタ 日本橋本店",
        "short": "本店",
        "id": "honten",
        "tag": "ポケカ買取",
        "icon": "DH",
        "color": "#1d4ed8",
        "url": "https://x.com/search?q=from%3Ads_nipponbashi%20ポケカ%20買取%20filter%3Aimages&src=typed_query&f=live",
    },
    {
        "name": "ドラスタ 日本橋2号店",
        "short": "ドラ2",
        "id": "dora2",
        "tag": "ポケカ買取",
        "icon": "D2",
        "color": "#7c3aed",
        "url": "https://x.com/search?q=from%3Ads_nipponbashi2%20ポケカ%20買取%20filter%3Aimages&src=typed_query&f=live",
    },
    {
        "name": "ドラスタ 日本橋3号店",
        "short": "ドラ3",
        "id": "dora3",
        "tag": "ポケカ買取",
        "icon": "D3",
        "color": "#dc2626",
        "url": "https://x.com/search?q=from%3Ads_nipponbashi3%20ポケカ%20買取%20filter%3Aimages&src=typed_query&f=live",
    },
    {
        "name": "ドラスタ なんさん通り店",
        "short": "なんさん",
        "id": "nansan",
        "tag": "ポケカ買取",
        "icon": "DN",
        "color": "#0891b2",
        "url": "https://x.com/search?q=from%3Ads_namba_nansan%20ポケカ%20買取%20filter%3Aimages&src=typed_query&f=live",
    },
    {
        "name": "晴れる屋2なんば",
        "short": "晴れる屋2",
        "id": "hareruya2",
        "tag": "ポケカ買取",
        "icon": "H",
        "color": "#059669",
        "url": "https://x.com/search?q=from%3Ahareruya2namba%20ポケカ%20買取%20filter%3Aimages&src=typed_query&f=live",
    },
    {
        "name": "カードラボなんば店",
        "short": "ラボなんば",
        "id": "labo-namba",
        "tag": "ポケカ買取",
        "icon": "L",
        "color": "#f59e0b",
        "url": "https://x.com/search?q=from%3Anamba_clabo%20ポケカ%20買取%20filter%3Aimages&src=typed_query&f=live",
    },
    {
        "name": "カードラボ大阪日本橋店",
        "short": "ラボ日本橋",
        "id": "labo-nihonbashi",
        "tag": "ポケカ買取",
        "icon": "LN",
        "color": "#ec4899",
        "url": "https://x.com/search?q=from%3Anipponbashi_lab%20ポケカ%20買取%20filter%3Aimages&src=typed_query&f=live",
    },
    {
        "name": "カードラボ販売買取センターNAMBA",
        "short": "ラボ買取",
        "id": "labo-kaitori",
        "tag": "ポケカ買取",
        "icon": "LC",
        "color": "#14b8a6",
        "url": "https://x.com/search?q=from%3Ananba2_labo%20ポケカ%20買取%20filter%3Aimages&src=typed_query&f=live",
    },
    {
        "name": "GIRAFULLなんば店",
        "short": "ジラなんば",
        "id": "gira-namba",
        "tag": "ポケカ買取",
        "icon": "G",
        "color": "#ea580c",
        "url": "https://x.com/search?q=from%3AGIRAFULL_Namba%20ポケカ%20買取%20filter%3Aimages&src=typed_query&f=live",
    },
    {
        "name": "GIRAFULL大阪日本橋店",
        "short": "ジラ日本橋",
        "id": "gira-nihonbashi",
        "tag": "ポケカ買取",
        "icon": "GN",
        "color": "#f97316",
        "url": "https://x.com/search?q=from%3Agirafull_o_n%20ポケカ%20買取%20filter%3Aimages&src=typed_query&f=live",
    },
    {
        "name": "GIRAFULLオタロード店",
        "short": "ジラオタ",
        "id": "gira-otaroad",
        "tag": "ポケカ買取",
        "icon": "GO",
        "color": "#fb923c",
        "url": "https://x.com/search?q=from%3AGIRAFULLOTARODO%20ポケカ%20買取%20filter%3Aimages&src=typed_query&f=live",
    },
]


def is_pokemon_buy_post(text):
    pokemon_words = [
        "ポケカ",
        "ポケモンカード",
        "ﾎﾟｹﾓﾝｶｰﾄﾞ",
        "pokemon",
        "Pokemon",
        "POKEMON",
    ]

    buy_words = [
        "買取",
        "高価買取",
        "買取表",
        "WANTED",
        "募集",
        "取扱強化",
        "お持ち込み",
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

    if len(summary) > 180:
        summary = summary[:180] + "..."

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


def build_html_start(updated_at):
    html_doc = """
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CardRadar</title>
<meta name="description" content="大阪・日本橋周辺のカードショップのポケカ買取情報をまとめて確認できるサイトです。">

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
    padding: 40px 20px 30px;
}

.header-inner {
    max-width: 1080px;
    margin: 0 auto;
}

.logo-row {
    display: flex;
    align-items: center;
    gap: 12px;
}

.site-icon {
    width: 46px;
    height: 46px;
    border-radius: 15px;
    background: #2563eb;
    display: grid;
    place-items: center;
    font-weight: 900;
    box-shadow: 0 10px 24px rgba(37,99,235,0.35);
}

.logo {
    font-size: 35px;
    font-weight: 850;
    margin: 0;
}

.lead {
    margin: 12px 0 0;
    color: #cbd5e1;
    font-size: 15px;
    line-height: 1.7;
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
    max-width: 1080px;
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
    font-weight: 600;
}

.nav-inner a:hover {
    background: #dbeafe;
    color: #1d4ed8;
}

main {
    max-width: 1080px;
    margin: 0 auto;
    padding: 26px 14px 44px;
}

.summary {
    background: white;
    border-radius: 20px;
    padding: 20px;
    margin-bottom: 24px;
    box-shadow: 0 10px 28px rgba(0,0,0,0.16);
}

.summary h2 {
    margin: 0 0 8px;
    font-size: 21px;
}

.summary p {
    margin: 0;
    color: #6b7280;
    font-size: 14px;
    line-height: 1.8;
}

.notice {
    margin-top: 14px;
    background: #f8fafc;
    border: 1px solid #e5e7eb;
    padding: 12px;
    border-radius: 14px;
    color: #475569;
    font-size: 13px;
}

.shop {
    background: white;
    border-radius: 22px;
    padding: 18px;
    margin-bottom: 30px;
    box-shadow: 0 10px 28px rgba(0,0,0,0.18);
    scroll-margin-top: 90px;
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

.shop h2 {
    margin: 0;
    font-size: 21px;
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
    max-width: 620px;
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

.empty {
    color: #6b7280;
    background: #f9fafb;
    padding: 14px;
    border-radius: 12px;
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

    .shop h2 {
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
        <p class="lead">大阪・日本橋周辺のカードショップ買取情報をまとめてチェック。Xの画像付きポケカ買取投稿を店舗別に表示しています。</p>
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

for shop in SEARCHES:
    html_doc += f'<a href="#{shop["id"]}">{shop["short"]}</a>\n'

html_doc += """
    </div>
</nav>

<main>

<section class="summary">
    <h2>最新のポケカ買取投稿まとめ</h2>
    <p>日本橋・なんば周辺のカードショップX投稿から、画像付きのポケカ買取情報を店舗別にまとめています。投稿本文の一部も表示することで、どんな買取表か分かりやすくしています。</p>
    <div class="notice">表示される投稿はXの埋め込み機能を利用しています。画像URLはOCR準備用としてdata.jsonに保存しますが、サイト上では再配布しません。</div>
</section>
"""

with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        user_data_dir=USER_DATA_DIR,
        headless=False
    )

    page = browser.new_page()

    for shop in SEARCHES:
        print("==============")
        print(shop["name"])
        print("==============")

        posts = []
        seen_urls = set()

        try:
            page.goto(shop["url"], wait_until="domcontentloaded", timeout=60000)
            time.sleep(8)

            tweets = page.locator("article")
            count = tweets.count()

            for i in range(min(count, CHECK_TWEETS_PER_SHOP)):
                tweet = tweets.nth(i)

                url = get_status_url(tweet)

                if not url:
                    continue

                if url in seen_urls:
                    continue

                text = tweet.inner_text()

                if not is_pokemon_buy_post(text):
                    continue

                image_urls = get_image_urls(tweet)

                if not image_urls:
                    continue

                summary = clean_tweet_text(text)

                seen_urls.add(url)

                post = {
                    "shop_name": shop["name"],
                    "shop_id": shop["id"],
                    "shop_short": shop["short"],
                    "tag": shop["tag"],
                    "tweet_url": url,
                    "summary": summary,
                    "image_urls": image_urls,
                    "image_count": len(image_urls),
                    "collected_at": updated_at,
                }

                posts.append(post)
                all_posts_data.append(post)

                print(url)
                print("画像数:", len(image_urls))

                if len(posts) >= MAX_TWEETS_PER_SHOP:
                    break

        except Exception as e:
            print("取得エラー:", e)

        html_doc += f"""
<section class="shop" id="{shop['id']}">
    <div class="shop-head">
        <div class="shop-title">
            <div class="shop-icon" style="background:{shop['color']};">{shop['icon']}</div>
            <div>
                <span class="badge">{shop['tag']}</span>
                <h2>{shop['name']}</h2>
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
                    <span class="image-count">画像{post['image_count']}枚</span>
                    <span>投稿内容</span>
                </div>
                <p>{safe_summary}</p>
            </div>

            <div class="tweet">
                <blockquote class="twitter-tweet">
                    <a href="{post['tweet_url']}"></a>
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
    print("取得投稿数:", len(all_posts_data))

    input("終了するにはEnter")

    browser.close()
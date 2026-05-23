from playwright.sync_api import sync_playwright
import time
import re
from datetime import datetime
import html as html_lib

# userdataをGit管理フォルダの外に出している場合
USER_DATA_DIR = "../userdata"

# もしログインが外れる・動かない場合は、下に変更してください
# USER_DATA_DIR = "userdata"

MAX_TWEETS_PER_SHOP = 3
CHECK_TWEETS_PER_SHOP = 12

SEARCHES = [
    {
        "name": "ドラスタ オタロード中央",
        "short": "オタ中",
        "tag": "ポケカ買取",
        "icon": "D",
        "color": "#2563eb",
        "url": "https://x.com/search?q=from%3Ads_otaroad_chuo%20ポケカ%20買取%20filter%3Aimages&src=typed_query",
    },
    {
        "name": "ドラスタ 日本橋2号店",
        "short": "ドラ2",
        "tag": "ポケカ買取",
        "icon": "D2",
        "color": "#7c3aed",
        "url": "https://x.com/search?q=from%3Ads_nipponbashi2%20ポケカ%20買取%20filter%3Aimages&src=typed_query",
    },
    {
        "name": "ドラスタ 日本橋3号店",
        "short": "ドラ3",
        "tag": "ポケカ買取",
        "icon": "D3",
        "color": "#dc2626",
        "url": "https://x.com/search?q=from%3Ads_nipponbashi3%20ポケカ%20買取%20filter%3Aimages&src=typed_query",
    },
    {
        "name": "ドラスタ くずはモール",
        "short": "くずは",
        "tag": "ポケカ買取",
        "icon": "K",
        "color": "#0891b2",
        "url": "https://x.com/search?q=from%3Ads_kuzuhamall%20ポケカ%20買取%20filter%3Aimages&src=typed_query",
    },
    {
        "name": "晴れる屋2なんば",
        "short": "晴れる屋2",
        "tag": "ポケカ買取",
        "icon": "H",
        "color": "#059669",
        "url": "https://x.com/search?q=from%3Ahareruya2namba%20ポケカ%20買取%20filter%3Aimages&src=typed_query",
    },
    {
        "name": "BIG MAGICなんば",
        "short": "BMなんば",
        "tag": "ポケカ買取",
        "icon": "B",
        "color": "#ea580c",
        "url": "https://x.com/search?q=from%3ABM_NAMBA%20ポケカ%20買取%20filter%3Aimages&src=typed_query",
    },
]

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

        # 数字だけ、いいね数・表示数っぽい行を除外
        if re.fullmatch(r"[0-9,\.万]+", line):
            continue

        # 店舗名だけの行は説明には不要
        if "ドラゴンスター" in line and len(line) < 25:
            continue

        if "晴れる屋2" in line and len(line) < 30:
            continue

        if "BIG MAGIC" in line and len(line) < 30:
            continue

        cleaned.append(line)

    summary = " ".join(cleaned)

    # 長すぎると見づらいので短くする
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


updated_at = datetime.now().strftime("%Y/%m/%d %H:%M")

html_doc = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CardRadar</title>

<style>
* {{
    box-sizing: border-box;
}}

html {{
    scroll-behavior: smooth;
}}

body {{
    margin: 0;
    font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
    background: #0f172a;
    color: #111827;
}}

header {{
    background:
        radial-gradient(circle at top left, rgba(59,130,246,0.38), transparent 34%),
        linear-gradient(135deg, #020617, #111827 55%, #1e293b);
    color: white;
    padding: 40px 20px 30px;
}}

.header-inner {{
    max-width: 1080px;
    margin: 0 auto;
}}

.logo-row {{
    display: flex;
    align-items: center;
    gap: 12px;
}}

.site-icon {{
    width: 46px;
    height: 46px;
    border-radius: 15px;
    background: #2563eb;
    display: grid;
    place-items: center;
    font-weight: 900;
    box-shadow: 0 10px 24px rgba(37,99,235,0.35);
}}

.logo {{
    font-size: 35px;
    font-weight: 850;
    margin: 0;
}}

.lead {{
    margin: 12px 0 0;
    color: #cbd5e1;
    font-size: 15px;
    line-height: 1.7;
}}

.meta {{
    margin-top: 16px;
    display: inline-block;
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.16);
    padding: 7px 12px;
    border-radius: 999px;
    font-size: 13px;
    color: #e5e7eb;
}}

nav {{
    max-width: 1080px;
    margin: -18px auto 0;
    padding: 0 14px;
    position: sticky;
    top: 0;
    z-index: 10;
}}

.nav-inner {{
    background: rgba(255,255,255,0.96);
    backdrop-filter: blur(10px);
    border-radius: 16px;
    padding: 10px;
    display: flex;
    gap: 8px;
    overflow-x: auto;
    box-shadow: 0 10px 26px rgba(0,0,0,0.18);
}}

.nav-inner a {{
    color: #111827;
    text-decoration: none;
    background: #f3f4f6;
    padding: 9px 13px;
    border-radius: 999px;
    font-size: 13px;
    white-space: nowrap;
    border: 1px solid #e5e7eb;
    font-weight: 600;
}}

.nav-inner a:hover {{
    background: #dbeafe;
    color: #1d4ed8;
}}

main {{
    max-width: 1080px;
    margin: 0 auto;
    padding: 26px 14px 44px;
}}

.summary {{
    background: white;
    border-radius: 20px;
    padding: 20px;
    margin-bottom: 24px;
    box-shadow: 0 10px 28px rgba(0,0,0,0.16);
}}

.summary h2 {{
    margin: 0 0 8px;
    font-size: 21px;
}}

.summary p {{
    margin: 0;
    color: #6b7280;
    font-size: 14px;
    line-height: 1.8;
}}

.notice {{
    margin-top: 14px;
    background: #f8fafc;
    border: 1px solid #e5e7eb;
    padding: 12px;
    border-radius: 14px;
    color: #475569;
    font-size: 13px;
}}

.shop {{
    background: white;
    border-radius: 22px;
    padding: 18px;
    margin-bottom: 30px;
    box-shadow: 0 10px 28px rgba(0,0,0,0.18);
    scroll-margin-top: 90px;
}}

.shop-head {{
    display: flex;
    justify-content: space-between;
    gap: 14px;
    align-items: center;
    border-bottom: 1px solid #e5e7eb;
    padding-bottom: 15px;
    margin-bottom: 18px;
}}

.shop-title {{
    display: flex;
    align-items: center;
    gap: 12px;
}}

.shop-icon {{
    width: 46px;
    height: 46px;
    border-radius: 16px;
    display: grid;
    place-items: center;
    color: white;
    font-weight: 900;
    flex: 0 0 auto;
}}

.shop h2 {{
    margin: 0;
    font-size: 21px;
}}

.badge {{
    display: inline-block;
    background: #dbeafe;
    color: #1d4ed8;
    padding: 5px 11px;
    border-radius: 999px;
    font-size: 13px;
    margin-bottom: 7px;
    font-weight: 700;
}}

.count {{
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    color: #374151;
    border-radius: 999px;
    padding: 8px 13px;
    font-size: 13px;
    white-space: nowrap;
}}

.tweet-list {{
    display: grid;
    grid-template-columns: 1fr;
    gap: 26px;
    justify-items: center;
}}

.post-card {{
    width: 100%;
    max-width: 620px;
    background: #f8fafc;
    border: 1px solid #e5e7eb;
    border-radius: 18px;
    padding: 14px;
}}

.post-summary {{
    margin-bottom: 12px;
}}

.post-summary-title {{
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 800;
    color: #111827;
    font-size: 14px;
    margin-bottom: 7px;
}}

.hot {{
    background: #fee2e2;
    color: #b91c1c;
    padding: 3px 8px;
    border-radius: 999px;
    font-size: 12px;
}}

.post-summary p {{
    margin: 0;
    color: #374151;
    font-size: 14px;
    line-height: 1.7;
}}

.tweet {{
    width: 100%;
    max-width: 560px;
    margin: 0 auto;
}}

.empty {{
    color: #6b7280;
    background: #f9fafb;
    padding: 14px;
    border-radius: 12px;
}}

footer {{
    text-align: center;
    color: #cbd5e1;
    padding: 34px 20px;
    font-size: 13px;
}}

@media (max-width: 640px) {{
    header {{
        padding: 30px 16px 26px;
    }}

    .logo {{
        font-size: 29px;
    }}

    .lead {{
        font-size: 14px;
    }}

    nav {{
        margin-top: -14px;
    }}

    .shop {{
        border-radius: 18px;
        padding: 14px;
    }}

    .shop-head {{
        display: block;
    }}

    .shop-title {{
        align-items: flex-start;
    }}

    .count {{
        display: inline-block;
        margin-top: 12px;
    }}

    .shop h2 {{
        font-size: 18px;
    }}

    .post-card {{
        padding: 12px;
    }}
}}
</style>
</head>

<body>

<header>
    <div class="header-inner">
        <div class="logo-row">
            <div class="site-icon">CR</div>
            <h1 class="logo">CardRadar</h1>
        </div>
        <p class="lead">大阪のカードショップ買取情報をまとめてチェック。Xの画像付きポケカ買取投稿を店舗別に表示しています。</p>
        <div class="meta">最終更新：{updated_at}</div>
    </div>
</header>

<nav>
    <div class="nav-inner">
"""

for shop in SEARCHES:
    html_doc += f'<a href="#{shop["short"]}">{shop["short"]}</a>\n'

html_doc += """
    </div>
</nav>

<main>

<section class="summary">
    <h2>最新のポケカ買取投稿まとめ</h2>
    <p>各カードショップのX投稿から、画像付きのポケカ買取情報を店舗別にまとめています。投稿本文の一部も表示することで、どんな買取表か分かりやすくしています。</p>
    <div class="notice">表示される投稿はXの埋め込み機能を利用しています。投稿が削除された場合やX側の仕様変更により表示されない場合があります。</div>
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
            page.goto(shop["url"])
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
                summary = clean_tweet_text(text)

                seen_urls.add(url)

                posts.append({
                    "url": url,
                    "summary": summary
                })

                print(url)

                if len(posts) >= MAX_TWEETS_PER_SHOP:
                    break

        except Exception as e:
            print("取得エラー:", e)

        html_doc += f"""
<section class="shop" id="{shop["short"]}">
    <div class="shop-head">
        <div class="shop-title">
            <div class="shop-icon" style="background:{shop["color"]};">{shop["icon"]}</div>
            <div>
                <span class="badge">{shop["tag"]}</span>
                <h2>{shop["name"]}</h2>
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
                    <span>投稿内容</span>
                </div>
                <p>{safe_summary}</p>
            </div>

            <div class="tweet">
                <blockquote class="twitter-tweet">
                    <a href="{post["url"]}"></a>
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

    html_doc += """
</main>

<footer>
    CardRadar - TCG買取情報まとめ
</footer>

<script async src="https://platform.twitter.com/widgets.js"></script>

</body>
</html>
"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_doc)

    print("")
    print("index.html を生成しました")

    input("終了するにはEnter")

    browser.close()
    
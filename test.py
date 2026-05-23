from playwright.sync_api import sync_playwright
import time
from datetime import datetime

SEARCHES = [
    {
        "name": "ドラスタ オタロード中央",
        "tag": "ポケカ買取",
        "url": "https://x.com/search?q=from%3Ads_otaroad_chuo%20ポケカ%20買取%20filter%3Aimages&src=typed_query"
    },
    {
        "name": "ドラスタ 日本橋2号店",
        "tag": "ポケカ買取",
        "url": "https://x.com/search?q=from%3Ads_nipponbashi2%20ポケカ%20買取%20filter%3Aimages&src=typed_query"
    },
    {
        "name": "ドラスタ 日本橋3号店",
        "tag": "ポケカ買取",
        "url": "https://x.com/search?q=from%3Ads_nipponbashi3%20ポケカ%20買取%20filter%3Aimages&src=typed_query"
    },
    {
        "name": "晴れる屋2なんば",
        "tag": "ポケカ買取",
        "url": "https://x.com/search?q=from%3Ahareruya2namba%20ポケカ%20買取%20filter%3Aimages&src=typed_query"
    }
]

updated_at = datetime.now().strftime("%Y/%m/%d %H:%M")

html = f"""
<!DOCTYPE html>
<html lang="ja">

<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CardRadar</title>

<style>
body {{
    font-family: system-ui, sans-serif;
    background: #f3f4f6;
    margin: 0;
    color: #111827;
}}

header {{
    background: linear-gradient(135deg, #111827, #1f2937);
    color: white;
    padding: 34px 20px;
}}

.header-inner {{
    max-width: 980px;
    margin: 0 auto;
}}

.logo {{
    font-size: 34px;
    font-weight: 800;
    letter-spacing: 0.5px;
    margin: 0;
}}

.lead {{
    margin: 10px 0 0;
    color: #d1d5db;
    font-size: 15px;
}}

.meta {{
    margin-top: 16px;
    display: inline-block;
    background: rgba(255,255,255,0.12);
    padding: 7px 12px;
    border-radius: 999px;
    font-size: 13px;
    color: #e5e7eb;
}}

main {{
    max-width: 980px;
    margin: 0 auto;
    padding: 26px 14px 40px;
}}

.summary {{
    background: white;
    border-radius: 16px;
    padding: 18px;
    margin-bottom: 24px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.07);
}}

.summary h2 {{
    margin: 0 0 8px;
    font-size: 20px;
}}

.summary p {{
    margin: 0;
    color: #6b7280;
    font-size: 14px;
    line-height: 1.7;
}}

.shop {{
    background: white;
    border-radius: 18px;
    padding: 18px;
    margin-bottom: 28px;
    box-shadow: 0 6px 18px rgba(0,0,0,0.08);
}}

.shop-head {{
    display: flex;
    justify-content: space-between;
    gap: 12px;
    align-items: flex-start;
    border-bottom: 1px solid #e5e7eb;
    padding-bottom: 14px;
    margin-bottom: 18px;
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
    margin-bottom: 8px;
    font-weight: 600;
}}

.count {{
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    color: #374151;
    border-radius: 999px;
    padding: 7px 12px;
    font-size: 13px;
    white-space: nowrap;
}}

.tweet {{
    margin: 0 auto 28px;
    max-width: 560px;
}}

.empty {{
    color: #6b7280;
    background: #f9fafb;
    padding: 14px;
    border-radius: 12px;
}}

footer {{
    text-align: center;
    color: #6b7280;
    padding: 34px 20px;
    font-size: 13px;
}}

@media (max-width: 600px) {{
    header {{
        padding: 28px 16px;
    }}

    .logo {{
        font-size: 28px;
    }}

    .shop-head {{
        display: block;
    }}

    .count {{
        display: inline-block;
        margin-top: 10px;
    }}
}}
</style>

</head>

<body>

<header>
    <div class="header-inner">
        <h1 class="logo">CardRadar</h1>
        <p class="lead">大阪のカードショップ買取情報をまとめてチェック</p>
        <div class="meta">最終更新：{updated_at}</div>
    </div>
</header>

<main>

<section class="summary">
    <h2>最新の買取投稿まとめ</h2>
    <p>各カードショップのX投稿から、画像付きの買取情報を店舗別に表示しています。</p>
</section>
"""

with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        user_data_dir="userdata",
        headless=False
    )

    page = browser.new_page()

    for shop in SEARCHES:
        print("==============")
        print(shop["name"])
        print("==============")

        page.goto(shop["url"])
        time.sleep(8)

        tweets = page.locator("article")
        count = tweets.count()

        added_urls = []

        for i in range(min(count, 8)):
            tweet = tweets.nth(i)
            links = tweet.locator("a")
            link_count = links.count()

            for j in range(link_count):
                href = links.nth(j).get_attribute("href")

                if href and "/status/" in href and "/photo/" not in href and "/analytics" not in href:
                    full_url = "https://x.com" + href if href.startswith("/") else href

                    if full_url not in added_urls:
                        added_urls.append(full_url)
                        print(full_url)

                    break

            if len(added_urls) >= 3:
                break

        html += f"""
<section class="shop">
    <div class="shop-head">
        <div>
            <span class="badge">{shop["tag"]}</span>
            <h2>{shop["name"]}</h2>
        </div>
        <div class="count">{len(added_urls)}件表示</div>
    </div>
"""

        if added_urls:
            for url in added_urls:
                html += f"""
    <div class="tweet">
        <blockquote class="twitter-tweet">
            <a href="{url}"></a>
        </blockquote>
    </div>
"""
        else:
            html += """
    <div class="empty">該当する投稿が見つかりませんでした。</div>
"""

        html += """
</section>
"""

    html += """
</main>

<footer>
    CardRadar - TCG買取情報まとめ
</footer>

<script async src="https://platform.twitter.com/widgets.js"></script>

</body>
</html>
"""

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print("")
    print("index.html を生成しました")

    input("終了するにはEnter")

    browser.close()
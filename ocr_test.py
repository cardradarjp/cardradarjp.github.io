import json
import re
from pathlib import Path
from io import BytesIO

import requests
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract


# Tesseract本体の場所
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# data.json の場所
DATA_FILE = "data.json"

# OCR用に画像を保存するフォルダ
IMAGE_DIR = Path("ocr_images")
IMAGE_DIR.mkdir(exist_ok=True)


# Tesseractの場所をPythonに教える
if Path(TESSERACT_PATH).exists():
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
else:
    print("Tesseractが見つかりません。パスを確認してください。")
    print(TESSERACT_PATH)
    exit()


def load_first_image_url():
    """
    data.json から最初の画像URLを1枚取得する
    """

    if not Path(DATA_FILE).exists():
        print("data.json が見つかりません。先に python test.py を実行してください。")
        return None

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    for post in data:
        image_urls = post.get("image_urls", [])

        if image_urls:
            return {
                "shop_name": post.get("shop_name"),
                "tweet_url": post.get("tweet_url"),
                "image_url": image_urls[0],
            }

    return None


def download_image(image_url):
    """
    画像URLから画像をダウンロードする
    """

    response = requests.get(image_url, timeout=30)
    response.raise_for_status()

    image = Image.open(BytesIO(response.content)).convert("RGB")

    original_path = IMAGE_DIR / "original_image.jpg"
    image.save(original_path)

    return image, original_path


def preprocess_image(image):
    """
    OCRしやすいように画像を加工する
    """

    # 画像を大きくする
    w, h = image.size
    image = image.resize((w * 2, h * 2))

    # グレースケール化
    image = image.convert("L")

    # コントラスト強化
    image = ImageEnhance.Contrast(image).enhance(2.0)

    # シャープ化
    image = image.filter(ImageFilter.SHARPEN)

    # 白黒化
    image = image.point(lambda x: 255 if x > 170 else 0)

    processed_path = IMAGE_DIR / "processed_image.jpg"
    image.save(processed_path)

    return image, processed_path


def get_ocr_language():
    """
    使えるOCR言語を確認する
    jpnがあれば日本語＋英語、なければ英語のみ
    """

    try:
        langs = pytesseract.get_languages(config="")
        print("使用可能なOCR言語:", langs)

        if "jpn" in langs:
            return "jpn+eng"

        return "eng"

    except Exception as e:
        print("OCR言語確認でエラー:", e)
        return "eng"


def run_ocr(image):
    """
    OCR実行
    """

    lang = get_ocr_language()
    print("使用するOCR言語:", lang)

    text = pytesseract.image_to_string(image, lang=lang)

    return text


def extract_prices(text):
    """
    OCRテキストから価格っぽい文字を抽出する
    """

    patterns = [
        r"[¥￥]\s?[0-9,]+",
        r"[0-9,]+\s?円",
        r"[0-9,]{4,}",
    ]

    prices = []

    for pattern in patterns:
        found = re.findall(pattern, text)
        prices.extend(found)

    unique_prices = []

    for price in prices:
        price = price.strip()

        if price not in unique_prices:
            unique_prices.append(price)

    return unique_prices


def main():
    print("ocr_test.py を開始します")
    print("")

    image_info = load_first_image_url()

    if not image_info:
        print("data.json に画像URLが見つかりませんでした。")
        return

    print("店舗:", image_info["shop_name"])
    print("投稿URL:", image_info["tweet_url"])
    print("画像URL:", image_info["image_url"])
    print("")

    image, original_path = download_image(image_info["image_url"])

    print("元画像を保存しました:", original_path)

    processed_image, processed_path = preprocess_image(image)

    print("OCR用画像を保存しました:", processed_path)
    print("OCRを実行します...")
    print("")

    ocr_text = run_ocr(processed_image)

    print("========== OCR結果 ==========")
    print(ocr_text)
    print("")

    prices = extract_prices(ocr_text)

    print("========== 抽出した価格 ==========")

    if prices:
        for price in prices:
            print(price)
    else:
        print("価格らしき文字は見つかりませんでした。")

    with open("ocr_result.txt", "w", encoding="utf-8") as f:
        f.write(ocr_text)

    print("")
    print("OCR結果を ocr_result.txt に保存しました。")


if __name__ == "__main__":
    main()
    
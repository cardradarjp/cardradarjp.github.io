from playwright.sync_api import sync_playwright
import time
import re
from datetime import datetime
import html as html_lib
import json
from urllib.parse import quote


USER_DATA_DIR = "../userdata"
# 動かない場合だけこちらに変更
# USER_DATA_DIR = "userdata"

MAX_TWEETS_PER_SOURCE = 3
CHECK_TWEETS_PER_SOURCE = 50
DEFAULT_SCROLL_ROUNDS = 5
DEFAULT_PAGE_WAIT_SEC = 10


TYPE_META = {
    "x_post_single": {
        "label": "シングル買取",
        "short_label": "シングル",
        "description": "SAR・SR・ARなど、カード単品の買取表を探せます。",
        "color": "#2563eb",
        "class": "type-single",
    },
    "x_post_box": {
        "label": "BOX買取",
        "short_label": "BOX",
        "description": "未開封BOX・シュリンク付きBOX・パック・カートン買取を探せます。",
        "color": "#16a34a",
        "class": "type-box",
    },
    "x_post_fixed": {
        "label": "定額買取",
        "short_label": "定額",
        "description": "ノーマル・RR・AR・汎用カード・ストレージなどのまとめ買取を探せます。",
        "color": "#f97316",
        "class": "type-fixed",
    },
    "online_price_list": {
        "label": "オンライン買取表",
        "short_label": "オンライン",
        "description": "公式サイト上の買取価格表を確認できます。",
        "color": "#7c3aed",
        "class": "type-online",
    },
    "market_price_link": {
        "label": "相場確認",
        "short_label": "相場",
        "description": "メルカリなどで販売相場を確認するための検索リンクです。",
        "color": "#dc2626",
        "class": "type-market",
    },
}


def x_search_url(account, words, images_only=True):
    query = f"from:{account} {words}"
    if images_only:
        query += " filter:images"
    return "https://x.com/search?q=" + quote(query) + "&src=typed_query&f=live"


def get_fetch_config(source):
    fetch = source.get("fetch", {})
    return {
        "check_tweets": fetch.get("check_tweets", CHECK_TWEETS_PER_SOURCE),
        "scroll_rounds": fetch.get("scroll_rounds", DEFAULT_SCROLL_ROUNDS),
        "page_wait_sec": fetch.get("page_wait_sec", DEFAULT_PAGE_WAIT_SEC),
        "images_only": fetch.get("images_only", True),
    }


SINGLE_WORDS = "(ポケカ OR ポケモンカード OR ポケモンカードゲーム OR Pokemon) (買取 OR 高価買取 OR 買取表 OR WANTED OR 募集 OR 取扱強化)"
BOX_WORDS = "(ポケカ OR ポケモンカード OR ポケモンカードゲーム OR Pokemon) (BOX OR box OR 未開封 OR シュリンク OR パック OR カートン OR ボックス) (買取 OR 高価買取 OR 募集)"
FIXED_WORDS = "(ポケカ OR ポケモンカード OR ポケモンカードゲーム OR Pokemon) (定額 OR 一律 OR まとめ買取 OR 最低保証 OR 保証買取 OR ノーマル OR RR OR AR OR 汎用 OR ストレージ OR 大量) (買取 OR 募集)"


SOURCES = [
    # =========================
    # シングル買取：大阪・日本橋・なんば
    # =========================
    {
        "source_type": "x_post_single",
        "name": "ドラスタ オタロード中央",
        "short": "オタ中",
        "id": "otachu-single",
        "area": "大阪・日本橋・なんば",
        "area_id": "osaka-nihonbashi",
        "prefecture": "大阪",
        "brand": "ドラゴンスター",
        "brand_id": "dragonstar",
        "game": "ポケカ",
        "icon": "D",
        "color": "#2563eb",
        "description": "ドラゴンスター オタロード中央店のポケカシングル買取表・高価買取情報を確認できます。",
        "url": x_search_url("ds_otaroad_chuo", SINGLE_WORDS),
    },
    {
        "source_type": "x_post_single",
        "name": "ドラスタ 日本橋本店",
        "short": "本店",
        "id": "honten-single",
        "area": "大阪・日本橋・なんば",
        "area_id": "osaka-nihonbashi",
        "prefecture": "大阪",
        "brand": "ドラゴンスター",
        "brand_id": "dragonstar",
        "game": "ポケカ",
        "icon": "DH",
        "color": "#1d4ed8",
        "description": "ドラゴンスター 日本橋本店のポケカシングル買取情報を確認できます。",
        "url": x_search_url("ds_nipponbashi", SINGLE_WORDS),
    },
    {
        "source_type": "x_post_single",
        "name": "ドラスタ 日本橋2号店",
        "short": "ドラ2",
        "id": "dora2-single",
        "area": "大阪・日本橋・なんば",
        "area_id": "osaka-nihonbashi",
        "prefecture": "大阪",
        "brand": "ドラゴンスター",
        "brand_id": "dragonstar",
        "game": "ポケカ",
        "icon": "D2",
        "color": "#7c3aed",
        "description": "ドラゴンスター 日本橋2号店のポケカ買取表・WANTED情報を確認できます。",
        "url": x_search_url("ds_nipponbashi2", SINGLE_WORDS),
    },
    {
        "source_type": "x_post_single",
        "name": "ドラスタ 日本橋3号店",
        "short": "ドラ3",
        "id": "dora3-single",
        "area": "大阪・日本橋・なんば",
        "area_id": "osaka-nihonbashi",
        "prefecture": "大阪",
        "brand": "ドラゴンスター",
        "brand_id": "dragonstar",
        "game": "ポケカ",
        "icon": "D3",
        "color": "#dc2626",
        "description": "ドラゴンスター 日本橋3号店のポケカ高価買取情報を確認できます。",
        "url": x_search_url(
            "ds_nipponbashi3",
            f"{SINGLE_WORDS} OR #ドラ3 OR ドラ3 OR 日本橋3号店 OR ORA3",
            images_only=False,
        ),
        "fetch": {
            "check_tweets": 60,
            "scroll_rounds": 8,
            "page_wait_sec": 12,
            "images_only": False,
        },
    },
    {
        "source_type": "x_post_single",
        "name": "ドラスタ なんさん通り店",
        "short": "なんさん",
        "id": "nansan-single",
        "area": "大阪・日本橋・なんば",
        "area_id": "osaka-nihonbashi",
        "prefecture": "大阪",
        "brand": "ドラゴンスター",
        "brand_id": "dragonstar",
        "game": "ポケカ",
        "icon": "DN",
        "color": "#0891b2",
        "description": "ドラゴンスター なんさん通り店のポケカ買取情報を確認できます。",
        "url": x_search_url("ds_namba_nansan", SINGLE_WORDS),
    },
    {
        "source_type": "x_post_single",
        "name": "晴れる屋2なんば",
        "short": "晴れる屋2",
        "id": "hareruya2-single",
        "area": "大阪・日本橋・なんば",
        "area_id": "osaka-nihonbashi",
        "prefecture": "大阪",
        "brand": "晴れる屋2",
        "brand_id": "hareruya2",
        "game": "ポケカ",
        "icon": "H",
        "color": "#059669",
        "description": "晴れる屋2なんば店のポケカ買取表・買取情報を確認できます。",
        "url": x_search_url("hareruya2namba", SINGLE_WORDS),
    },
    {
        "source_type": "x_post_single",
        "name": "カードラボなんば店",
        "short": "ラボなんば",
        "id": "labo-namba-single",
        "area": "大阪・日本橋・なんば",
        "area_id": "osaka-nihonbashi",
        "prefecture": "大阪",
        "brand": "カードラボ",
        "brand_id": "cardlabo",
        "game": "ポケカ",
        "icon": "L",
        "color": "#f59e0b",
        "description": "カードラボなんば店のポケカ買取情報を確認できます。",
        "url": x_search_url("namba_clabo", SINGLE_WORDS),
    },
    {
        "source_type": "x_post_single",
        "name": "カードラボ大阪日本橋店",
        "short": "ラボ日本橋",
        "id": "labo-nihonbashi-single",
        "area": "大阪・日本橋・なんば",
        "area_id": "osaka-nihonbashi",
        "prefecture": "大阪",
        "brand": "カードラボ",
        "brand_id": "cardlabo",
        "game": "ポケカ",
        "icon": "LN",
        "color": "#ec4899",
        "description": "カードラボ大阪日本橋店のポケカ買取情報を確認できます。",
        "url": x_search_url("nipponbashi_lab", SINGLE_WORDS),
    },
    {
        "source_type": "x_post_single",
        "name": "カードラボ販売買取センターNAMBA",
        "short": "ラボ買取",
        "id": "labo-kaitori-single",
        "area": "大阪・日本橋・なんば",
        "area_id": "osaka-nihonbashi",
        "prefecture": "大阪",
        "brand": "カードラボ",
        "brand_id": "cardlabo",
        "game": "ポケカ",
        "icon": "LC",
        "color": "#14b8a6",
        "description": "カードラボ販売買取センターNAMBAのポケカ買取情報を確認できます。",
        "url": x_search_url("nanba2_labo", SINGLE_WORDS),
    },
    {
        "source_type": "x_post_single",
        "name": "GIRAFULLなんば店",
        "short": "ジラなんば",
        "id": "gira-namba-single",
        "area": "大阪・日本橋・なんば",
        "area_id": "osaka-nihonbashi",
        "prefecture": "大阪",
        "brand": "GIRAFULL",
        "brand_id": "girafull",
        "game": "ポケカ",
        "icon": "G",
        "color": "#ea580c",
        "description": "GIRAFULLなんば店のポケカ買取情報を確認できます。",
        "url": x_search_url("GIRAFULL_Namba", SINGLE_WORDS),
    },
    {
        "source_type": "x_post_single",
        "name": "GIRAFULL大阪日本橋店",
        "short": "ジラ日本橋",
        "id": "gira-nihonbashi-single",
        "area": "大阪・日本橋・なんば",
        "area_id": "osaka-nihonbashi",
        "prefecture": "大阪",
        "brand": "GIRAFULL",
        "brand_id": "girafull",
        "game": "ポケカ",
        "icon": "GN",
        "color": "#f97316",
        "description": "GIRAFULL大阪日本橋店のポケカ買取情報を確認できます。",
        "url": x_search_url("girafull_o_n", SINGLE_WORDS),
    },
    {
        "source_type": "x_post_single",
        "name": "GIRAFULLオタロード店",
        "short": "ジラオタ",
        "id": "gira-otaroad-single",
        "area": "大阪・日本橋・なんば",
        "area_id": "osaka-nihonbashi",
        "prefecture": "大阪",
        "brand": "GIRAFULL",
        "brand_id": "girafull",
        "game": "ポケカ",
        "icon": "GO",
        "color": "#fb923c",
        "description": "GIRAFULLオタロード店のポケカ買取情報を確認できます。",
        "url": x_search_url("GIRAFULLOTARODO", SINGLE_WORDS),
    },

    # =========================
    # 追加店舗：シングル / BOX / 定額
    # XアカウントIDが違う場合は、該当sourceのurl内アカウント名を修正してください
    # =========================
    {
        "source_type": "x_post_single",
        "name": "アムタフ シングル買取",
        "short": "アムタフ単品",
        "id": "amtaf-single",
        "area": "大阪・日本橋・なんば",
        "area_id": "osaka-nihonbashi",
        "prefecture": "大阪",
        "brand": "アムタフ",
        "brand_id": "amtaf",
        "game": "ポケカ",
        "icon": "A",
        "color": "#0f766e",
        "description": "アムタフのポケカシングルカード買取投稿を確認できます。",
        "url": x_search_url("AMTAF_SHOP", SINGLE_WORDS),
    },
    {
        "source_type": "x_post_box",
        "name": "アムタフ BOX買取",
        "short": "アムタフBOX",
        "id": "amtaf-box",
        "area": "大阪・日本橋・なんば",
        "area_id": "osaka-nihonbashi",
        "prefecture": "大阪",
        "brand": "アムタフ",
        "brand_id": "amtaf",
        "game": "ポケカ",
        "icon": "AB",
        "color": "#16a34a",
        "description": "アムタフのポケカ未開封BOX・パック買取投稿を確認できます。",
        "url": x_search_url("AMTAF_SHOP", BOX_WORDS),
    },
    {
        "source_type": "x_post_fixed",
        "name": "アムタフ 定額買取",
        "short": "アムタフ定額",
        "id": "amtaf-fixed",
        "area": "大阪・日本橋・なんば",
        "area_id": "osaka-nihonbashi",
        "prefecture": "大阪",
        "brand": "アムタフ",
        "brand_id": "amtaf",
        "game": "ポケカ",
        "icon": "AF",
        "color": "#f97316",
        "description": "アムタフの定額買取・まとめ買取系投稿を確認できます。",
        "url": x_search_url("AMTAF_SHOP", FIXED_WORDS),
    },
    {
        "source_type": "x_post_single",
        "name": "GOTCHA! シングル買取",
        "short": "GOTCHA単品",
        "id": "gotcha-single",
        "area": "大阪・日本橋・なんば",
        "area_id": "osaka-nihonbashi",
        "prefecture": "大阪",
        "brand": "GOTCHA!",
        "brand_id": "gotcha",
        "game": "ポケカ",
        "icon": "G",
        "color": "#0ea5e9",
        "description": "GOTCHA!のポケカシングル買取投稿を確認できます。",
        "url": x_search_url("cardshop_gotcha", SINGLE_WORDS),
    },
    {
        "source_type": "x_post_box",
        "name": "GOTCHA! BOX買取",
        "short": "GOTCHA BOX",
        "id": "gotcha-box",
        "area": "大阪・日本橋・なんば",
        "area_id": "osaka-nihonbashi",
        "prefecture": "大阪",
        "brand": "GOTCHA!",
        "brand_id": "gotcha",
        "game": "ポケカ",
        "icon": "GB",
        "color": "#16a34a",
        "description": "GOTCHA!のポケカ未開封BOX・パック買取投稿を確認できます。",
        "url": x_search_url("cardshop_gotcha", BOX_WORDS),
    },
    {
        "source_type": "x_post_single",
        "name": "KURO シングル買取",
        "short": "KURO単品",
        "id": "kuro-single",
        "area": "大阪・日本橋・なんば",
        "area_id": "osaka-nihonbashi",
        "prefecture": "大阪",
        "brand": "KURO",
        "brand_id": "kuro",
        "game": "ポケカ",
        "icon": "K",
        "color": "#111827",
        "description": "トレカショップKUROのポケカシングル買取投稿を確認できます。",
        "url": x_search_url("kuro_tcg", SINGLE_WORDS),
    },
    {
        "source_type": "x_post_box",
        "name": "KURO BOX買取",
        "short": "KURO BOX",
        "id": "kuro-box",
        "area": "大阪・日本橋・なんば",
        "area_id": "osaka-nihonbashi",
        "prefecture": "大阪",
        "brand": "KURO",
        "brand_id": "kuro",
        "game": "ポケカ",
        "icon": "KB",
        "color": "#16a34a",
        "description": "トレカショップKUROのポケカ未開封BOX・パック・カートン買取投稿を確認できます。",
        "url": x_search_url("kuro_tcg", BOX_WORDS),
    },
    {
        "source_type": "x_post_single",
        "name": "買取ミミ シングル買取",
        "short": "ミミ単品",
        "id": "mimi-single",
        "area": "大阪・日本橋・なんば",
        "area_id": "osaka-nihonbashi",
        "prefecture": "大阪",
        "brand": "買取ミミ",
        "brand_id": "mimi",
        "game": "ポケカ",
        "icon": "M",
        "color": "#db2777",
        "description": "買取ミミのポケカシングル買取投稿を確認できます。",
        "url": x_search_url("mimi_kaitori", SINGLE_WORDS),
    },
    {
        "source_type": "x_post_box",
        "name": "買取ミミ BOX買取",
        "short": "ミミBOX",
        "id": "mimi-box",
        "area": "大阪・日本橋・なんば",
        "area_id": "osaka-nihonbashi",
        "prefecture": "大阪",
        "brand": "買取ミミ",
        "brand_id": "mimi",
        "game": "ポケカ",
        "icon": "MB",
        "color": "#16a34a",
        "description": "買取ミミのポケカ未開封BOX・パック買取投稿を確認できます。",
        "url": x_search_url(
            "mimi_kaitori",
            "(ポケカ OR ポケモンカード) (未開封 OR シュリンク OR カートン OR ボックス OR BOX OR box) (買取 OR 募集 OR 強化)",
            images_only=False,
        ),
        "fetch": {
            "check_tweets": 60,
            "scroll_rounds": 8,
            "page_wait_sec": 12,
            "images_only": False,
        },
    },
    {
        "source_type": "x_post_fixed",
        "name": "買取ミミ 定額買取",
        "short": "ミミ定額",
        "id": "mimi-fixed",
        "area": "大阪・日本橋・なんば",
        "area_id": "osaka-nihonbashi",
        "prefecture": "大阪",
        "brand": "買取ミミ",
        "brand_id": "mimi",
        "game": "ポケカ",
        "icon": "MF",
        "color": "#f97316",
        "description": "買取ミミの定額買取・まとめ買取系投稿を確認できます。",
        "url": x_search_url("mimi_kaitori", FIXED_WORDS),
    },
    {
        "source_type": "x_post_single",
        "name": "買取アイアイ シングル買取",
        "short": "アイアイ単品",
        "id": "aiai-single",
        "area": "大阪・日本橋・なんば",
        "area_id": "osaka-nihonbashi",
        "prefecture": "大阪",
        "brand": "買取アイアイ",
        "brand_id": "aiai",
        "game": "ポケカ",
        "icon": "I",
        "color": "#9333ea",
        "description": "買取アイアイのポケカシングル買取投稿を確認できます。",
        "url": x_search_url("KAITORIAIAI", SINGLE_WORDS),
    },
    {
        "source_type": "x_post_box",
        "name": "買取アイアイ BOX買取",
        "short": "アイアイBOX",
        "id": "aiai-box",
        "area": "大阪・日本橋・なんば",
        "area_id": "osaka-nihonbashi",
        "prefecture": "大阪",
        "brand": "買取アイアイ",
        "brand_id": "aiai",
        "game": "ポケカ",
        "icon": "IB",
        "color": "#16a34a",
        "description": "買取アイアイのポケカ未開封BOX・パック買取投稿を確認できます。",
        "url": x_search_url("KAITORIAIAI", BOX_WORDS),
    },
    {
        "source_type": "x_post_fixed",
        "name": "買取アイアイ 定額買取",
        "short": "アイアイ定額",
        "id": "aiai-fixed",
        "area": "大阪・日本橋・なんば",
        "area_id": "osaka-nihonbashi",
        "prefecture": "大阪",
        "brand": "買取アイアイ",
        "brand_id": "aiai",
        "game": "ポケカ",
        "icon": "IF",
        "color": "#f97316",
        "description": "買取アイアイの定額買取・まとめ買取系投稿を確認できます。",
        "url": x_search_url("KAITORIAIAI", FIXED_WORDS),
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
        "icon": "C",
        "color": "#7c3aed",
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
        "icon": "F",
        "color": "#7c3aed",
        "official_url": "https://fullahead-buy.com/",
        "description": "ポケモンカードゲームを含む各種TCGの高価買取リストを確認できます。",
    },

    # =========================
    # 相場確認リンク
    # =========================
    {
        "source_type": "market_price_link",
        "name": "メルカリ ポケカ相場",
        "short": "メルカリ",
        "id": "mercari-pokemon",
        "area": "相場確認",
        "area_id": "market",
        "prefecture": "相場確認",
        "brand": "メルカリ",
        "brand_id": "mercari",
        "game": "ポケカ",
        "icon": "M",
        "color": "#dc2626",
        "official_url": "https://jp.mercari.com/search?keyword=%E3%83%9D%E3%82%B1%E3%82%AB",
        "description": "メルカリでポケカの販売相場を確認できます。CardRadarでは商品情報や価格は取得せず、検索リンクのみ掲載します。",
    },
    {
        "source_type": "market_price_link",
        "name": "メルカリ ポケカBOX相場",
        "short": "メルカリBOX",
        "id": "mercari-box",
        "area": "相場確認",
        "area_id": "market",
        "prefecture": "相場確認",
        "brand": "メルカリ",
        "brand_id": "mercari",
        "game": "ポケカ",
        "icon": "MB",
        "color": "#dc2626",
        "official_url": "https://jp.mercari.com/search?keyword=%E3%83%9D%E3%82%B1%E3%82%AB%20BOX%20%E6%9C%AA%E9%96%8B%E5%B0%81",
        "description": "メルカリでポケカ未開封BOX・パックの販売相場を確認できます。自動取得は行わず、検索リンクのみ掲載します。",
    },
]


def is_likely_single_post(text):
    single_markers = [
        "BOX以外",
        "box以外",
        "ボックス以外",
        "シングルカード",
        "シングル買取",
        "シングル ",
        "PSA鑑定",
        "PSA全力",
        "WANTED",
        "高価買取表",
        "買取表更新",
        "取扱強化",
        "超本気買取",
        "(SAR)",
        "(SR)",
        "(AR)",
        "(MUR)",
        "(RR)",
        "[SAR]",
        "[SR]",
        "ex(SAR)",
        "ex(SR)",
        "ex(AR)",
        "】買取￥",
        "買取￥",
        "ﾒｶﾞ",
        "メガダークライ",
    ]

    return any(marker in text for marker in single_markers)


def is_box_post(text):
    if is_likely_single_post(text):
        return False

    box_markers = [
        "ポケモンカードBOX",
        "ポケカBOX",
        "BOX買取",
        "BOX 買取",
        "BOX買取表",
        "ボックス買取",
        "未開封BOX",
        "未開封 BOX",
        "未開封】",
        "シュリンク付",
        "シュリンクあり",
        "シュリンクなし",
        "シュリンク無",
        "シュリンク ",
        "カートン",
        "1BOX",
        "BOX強化",
        "BOX 強化",
        "新弾BOX",
        "BOXシュリンク",
    ]

    if any(marker in text for marker in box_markers):
        return True

    if re.search(r"BOX", text, re.IGNORECASE):
        if re.search(r"BOX\s*以外", text, re.IGNORECASE):
            return False
        if any(word in text for word in ["買取", "未開封", "シュリンク", "カートン", "パック", "ボックス"]):
            return True

    return False


def is_target_post(text, source_type):
    pokemon_words = [
        "ポケカ",
        "ポケモンカード",
        "ポケモンカードゲーム",
        "ﾎﾟｹﾓﾝｶｰﾄﾞ",
        "pokemon",
        "Pokemon",
        "POKEMON",
        "#ドラ3",
        "ドラ3",
        "ORA3",
        "3号店",
    ]

    buy_words = [
        "買取",
        "高価買取",
        "買取表",
        "WANTED",
        "募集",
        "取扱強化",
        "お持ち込み",
        "超本気買取",
        "買取情報",
        "更新Ver",
        "更新ver",
    ]

    fixed_words = [
        "定額",
        "一律",
        "まとめ買取",
        "最低保証",
        "保証買取",
        "ノーマル",
        "RR",
        "AR",
        "CHR",
        "汎用",
        "ストレージ",
        "大量",
        "束",
        "買取保証",
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

    if not (has_pokemon and has_buy):
        return False

    if source_type == "x_post_box":
        return is_box_post(text)

    if source_type == "x_post_fixed":
        return any(word in text for word in fixed_words)

    return True


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

        if "買取ミミ" in line and len(line) < 35:
            continue

        if "ドラゴンスター" in line and "3号店" in line and len(line) < 30:
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
            return "https://x.com" + href if href.startswith("/") else href

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


def load_search_results(page, fetch_config):
    page.wait_for_timeout(fetch_config["page_wait_sec"] * 1000)

    for _ in range(fetch_config["scroll_rounds"]):
        page.mouse.wheel(0, 1600)
        page.wait_for_timeout(1500)

    page.wait_for_timeout(2000)


def get_unique_areas():
    areas = []

    for source in SOURCES:
        if not any(area["area_id"] == source["area_id"] for area in areas):
            areas.append({
                "area": source["area"],
                "area_id": source["area_id"],
            })

    return areas


def get_sources_by_area(area_id):
    return [source for source in SOURCES if source["area_id"] == area_id]


def get_unique_brands():
    brands = []

    for source in SOURCES:
        if not any(brand["brand_id"] == source["brand_id"] for brand in brands):
            brands.append({
                "brand": source["brand"],
                "brand_id": source["brand_id"],
            })

    return brands


def get_sources_by_type(source_type):
    return [source for source in SOURCES if source["source_type"] == source_type]


def make_search_text(source):
    values = [
        source.get("name", ""),
        source.get("short", ""),
        source.get("area", ""),
        source.get("prefecture", ""),
        source.get("brand", ""),
        source.get("game", ""),
        TYPE_META[source.get("source_type", "")]["label"],
        source.get("description", ""),
    ]
    return " ".join(values)


def source_badge(source_type):
    meta = TYPE_META[source_type]
    return f'<span class="type-badge {meta["class"]}">{meta["label"]}</span>'


def build_html_start(updated_at):
    html_doc = """
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">

<title>CardRadar｜ポケカ買取表を地域・店舗・買取タイプ別に探す</title>
<meta name="description" content="CardRadarは、ポケカ買取表を地域・店舗・買取タイプ別に探せる買取情報まとめサイトです。シングル買取、BOX買取、定額買取、オンライン買取表、相場確認リンクを掲載。">

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
    background:
        radial-gradient(circle at top left, rgba(37,99,235,0.20), transparent 28%),
        radial-gradient(circle at top right, rgba(124,58,237,0.18), transparent 28%),
        #0f172a;
    color: #111827;
}

header {
    color: white;
    padding: 46px 20px 34px;
}

.header-inner {
    max-width: 1180px;
    margin: 0 auto;
}

.logo-row {
    display: flex;
    align-items: center;
    gap: 13px;
}

.site-icon {
    width: 50px;
    height: 50px;
    border-radius: 17px;
    background: linear-gradient(135deg, #2563eb, #7c3aed);
    display: grid;
    place-items: center;
    font-weight: 950;
    box-shadow: 0 16px 32px rgba(37,99,235,0.35);
}

.logo {
    font-size: 38px;
    font-weight: 900;
    margin: 0;
    letter-spacing: -0.04em;
}

.hero-title {
    margin: 18px 0 0;
    font-size: 30px;
    line-height: 1.35;
    font-weight: 900;
    letter-spacing: -0.04em;
}

.lead {
    margin: 12px 0 0;
    color: #cbd5e1;
    font-size: 15px;
    line-height: 1.85;
    max-width: 920px;
}

.hero-tags {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-top: 18px;
}

.hero-tag {
    background: rgba(255,255,255,0.11);
    border: 1px solid rgba(255,255,255,0.16);
    color: #e5e7eb;
    padding: 7px 11px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 800;
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
    max-width: 1180px;
    margin: -18px auto 0;
    padding: 0 14px;
    position: sticky;
    top: 0;
    z-index: 10;
}

.nav-inner {
    background: rgba(255,255,255,0.96);
    backdrop-filter: blur(10px);
    border-radius: 18px;
    padding: 10px;
    display: flex;
    gap: 8px;
    overflow-x: auto;
    box-shadow: 0 14px 32px rgba(0,0,0,0.22);
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
    font-weight: 800;
}

main {
    max-width: 1180px;
    margin: 0 auto;
    padding: 28px 14px 46px;
}

.panel {
    background: rgba(255,255,255,0.98);
    border-radius: 24px;
    padding: 22px;
    margin-bottom: 26px;
    box-shadow: 0 14px 34px rgba(0,0,0,0.18);
    border: 1px solid rgba(255,255,255,0.7);
}

.panel h2 {
    margin: 0 0 8px;
    font-size: 23px;
    letter-spacing: -0.02em;
}

.panel p {
    margin: 0;
    color: #4b5563;
    font-size: 14px;
    line-height: 1.9;
}

.type-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 12px;
    margin-top: 18px;
}

.type-card {
    border: 1px solid #e5e7eb;
    border-radius: 18px;
    padding: 14px;
    background: #f8fafc;
    cursor: pointer;
    transition: transform .12s ease, box-shadow .12s ease;
}

.type-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 22px rgba(0,0,0,0.10);
}

.type-card strong {
    display: block;
    font-size: 15px;
    margin-bottom: 6px;
}

.type-card span {
    display: block;
    font-size: 12px;
    color: #64748b;
    line-height: 1.55;
}

.search-input {
    width: 100%;
    padding: 15px 16px;
    border-radius: 16px;
    border: 1px solid #d1d5db;
    font-size: 16px;
    margin: 14px 0 16px;
    outline: none;
}

.search-input:focus {
    border-color: #2563eb;
    box-shadow: 0 0 0 4px rgba(37,99,235,0.12);
}

.filter-group {
    margin-top: 15px;
}

.filter-title {
    font-weight: 900;
    font-size: 14px;
    margin-bottom: 9px;
    color: #111827;
}

.filter-buttons {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
}

.filter-button {
    border: 1px solid #d1d5db;
    background: #f9fafb;
    color: #111827;
    border-radius: 999px;
    padding: 8px 12px;
    font-weight: 800;
    cursor: pointer;
    font-size: 13px;
}

.filter-button.active {
    background: #2563eb;
    color: white;
    border-color: #2563eb;
}

.filter-status {
    margin-top: 16px;
    color: #334155;
    font-size: 14px;
    font-weight: 900;
}

.reset-button {
    margin-top: 14px;
    border: none;
    background: #111827;
    color: white;
    border-radius: 13px;
    padding: 10px 14px;
    font-weight: 900;
    cursor: pointer;
}

.notice {
    margin-top: 14px;
    background: #f8fafc;
    border: 1px solid #e5e7eb;
    padding: 12px;
    border-radius: 14px;
    color: #475569;
    font-size: 13px;
    line-height: 1.75;
}

.section-title {
    color: white;
    margin: 34px 0 16px;
    scroll-margin-top: 95px;
}

.section-title h2 {
    font-size: 28px;
    margin: 0;
    letter-spacing: -0.04em;
}

.section-title p {
    color: #cbd5e1;
    margin: 8px 0 0;
    font-size: 14px;
    line-height: 1.75;
}

.source-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 18px;
}

.source-card {
    background: rgba(255,255,255,0.98);
    border-radius: 22px;
    padding: 16px;
    box-shadow: 0 12px 30px rgba(0,0,0,0.18);
    border: 1px solid rgba(255,255,255,0.75);
}

.source-head {
    display: flex;
    gap: 12px;
    align-items: flex-start;
    justify-content: space-between;
    border-bottom: 1px solid #e5e7eb;
    padding-bottom: 13px;
    margin-bottom: 14px;
}

.source-main {
    display: flex;
    gap: 12px;
    align-items: flex-start;
}

.source-icon {
    width: 46px;
    height: 46px;
    border-radius: 16px;
    display: grid;
    place-items: center;
    color: white;
    font-weight: 950;
    flex: 0 0 auto;
}

.source-card h3 {
    margin: 4px 0 0;
    font-size: 19px;
    letter-spacing: -0.02em;
}

.source-description {
    margin: 6px 0 0;
    color: #6b7280;
    font-size: 13px;
    line-height: 1.65;
}

.label-row {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
}

.type-badge,
.area-badge,
.brand-badge {
    display: inline-block;
    padding: 4px 9px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 900;
}

.area-badge {
    background: #e0f2fe;
    color: #0369a1;
}

.brand-badge {
    background: #f1f5f9;
    color: #334155;
}

.type-single {
    background: #dbeafe;
    color: #1d4ed8;
}

.type-box {
    background: #dcfce7;
    color: #166534;
}

.type-fixed {
    background: #ffedd5;
    color: #c2410c;
}

.type-online {
    background: #ede9fe;
    color: #6d28d9;
}

.type-market {
    background: #fee2e2;
    color: #b91c1c;
}

.count {
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    color: #374151;
    border-radius: 999px;
    padding: 8px 11px;
    font-size: 12px;
    font-weight: 900;
    white-space: nowrap;
}

.post-list {
    display: grid;
    gap: 16px;
}

.post-card {
    background: #f8fafc;
    border: 1px solid #e5e7eb;
    border-radius: 18px;
    padding: 13px;
}

.post-summary-title {
    display: flex;
    align-items: center;
    gap: 7px;
    font-weight: 900;
    color: #111827;
    font-size: 13px;
    margin-bottom: 7px;
    flex-wrap: wrap;
}

.hot {
    background: #fee2e2;
    color: #b91c1c;
    padding: 3px 8px;
    border-radius: 999px;
    font-size: 11px;
}

.image-count {
    background: #dcfce7;
    color: #166534;
    padding: 3px 8px;
    border-radius: 999px;
    font-size: 11px;
}

.post-card p {
    margin: 0 0 10px;
    color: #374151;
    font-size: 13px;
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
    font-weight: 900;
    font-size: 14px;
}

.empty {
    color: #6b7280;
    background: #f9fafb;
    padding: 14px;
    border-radius: 12px;
    font-size: 13px;
}

.cta-box {
    background:
        radial-gradient(circle at top left, rgba(37,99,235,0.15), transparent 34%),
        #ffffff;
    border-radius: 24px;
    padding: 22px;
    margin-top: 34px;
    box-shadow: 0 14px 34px rgba(0,0,0,0.18);
}

.cta-box h2 {
    margin: 0 0 8px;
    font-size: 23px;
}

.cta-box p {
    margin: 0;
    color: #4b5563;
    font-size: 14px;
    line-height: 1.85;
}

footer {
    text-align: center;
    color: #cbd5e1;
    padding: 34px 20px;
    font-size: 13px;
}

.hidden-by-filter {
    display: none !important;
}

@media (max-width: 920px) {
    .type-grid,
    .source-grid {
        grid-template-columns: 1fr;
    }
}

@media (max-width: 640px) {
    header {
        padding: 30px 16px 26px;
    }

    .logo {
        font-size: 30px;
    }

    .hero-title {
        font-size: 24px;
    }

    .lead {
        font-size: 14px;
    }

    nav {
        margin-top: -14px;
    }

    .panel,
    .source-card,
    .cta-box {
        border-radius: 18px;
        padding: 15px;
    }

    .source-head {
        display: block;
    }

    .count {
        display: inline-block;
        margin-top: 12px;
    }

    .source-card h3 {
        font-size: 18px;
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
        <h2 class="hero-title">ポケカ買取表を、最短で探す。</h2>
        <p class="lead">
            CardRadarは、ポケカのシングル買取・BOX買取・定額買取・オンライン買取表・相場確認リンクを、
            地域・店舗・買取タイプ別にまとめて探せる買取情報ツールです。
        </p>
        <div class="hero-tags">
            <span class="hero-tag">シングル買取</span>
            <span class="hero-tag">BOX買取</span>
            <span class="hero-tag">定額買取</span>
            <span class="hero-tag">オンライン買取表</span>
            <span class="hero-tag">相場確認</span>
        </div>
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

<script>
const filters = {
    area: "all",
    brand: "all",
    source: "all",
    search: ""
};

function setFilter(type, value) {
    filters[type] = value;

    document.querySelectorAll(`[data-filter-type="${type}"]`).forEach(button => {
        button.classList.remove("active");
        if (button.dataset.filterValue === value) {
            button.classList.add("active");
        }
    });

    applyFilters();
}

function resetFilters() {
    filters.area = "all";
    filters.brand = "all";
    filters.source = "all";
    filters.search = "";

    document.getElementById("shopSearch").value = "";

    document.querySelectorAll(".filter-button").forEach(button => {
        button.classList.remove("active");
        if (button.dataset.filterValue === "all") {
            button.classList.add("active");
        }
    });

    applyFilters();
}

function applyFilters() {
    const searchInput = document.getElementById("shopSearch");
    filters.search = searchInput.value.trim().toLowerCase();

    const cards = document.querySelectorAll(".source-card");
    let visibleCount = 0;

    cards.forEach(card => {
        const area = card.dataset.area;
        const brand = card.dataset.brand;
        const source = card.dataset.source;
        const searchText = card.dataset.search.toLowerCase();

        const areaOk = filters.area === "all" || filters.area === area;
        const brandOk = filters.brand === "all" || filters.brand === brand;
        const sourceOk = filters.source === "all" || filters.source === source;
        const searchOk = !filters.search || searchText.includes(filters.search);

        if (areaOk && brandOk && sourceOk && searchOk) {
            card.classList.remove("hidden-by-filter");
            visibleCount++;
        } else {
            card.classList.add("hidden-by-filter");
        }
    });

    updateSectionVisibility();
    document.getElementById("visibleCount").textContent = visibleCount;
}

function updateSectionVisibility() {
    document.querySelectorAll(".type-section").forEach(section => {
        const visibleCards = section.querySelectorAll(".source-card:not(.hidden-by-filter)");
        section.style.display = visibleCards.length > 0 ? "" : "none";
    });
}

document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("shopSearch").addEventListener("input", applyFilters);
    applyFilters();
});
</script>

</body>
</html>
"""


def render_filter_box():
    html_doc = """
<section class="panel">
    <h2>何を探しますか？</h2>
    <p>買取タイプ・地域・ブランド・店舗名で絞り込みできます。店舗数が増えても、目的の買取情報だけをすぐ探せます。</p>

    <div class="type-grid">
"""

    for source_type, meta in TYPE_META.items():
        html_doc += f"""
        <div class="type-card" onclick="setFilter('source', '{source_type}')">
            <strong>{meta["label"]}</strong>
            <span>{meta["description"]}</span>
        </div>
"""

    html_doc += """
    </div>

    <input
        id="shopSearch"
        class="search-input"
        type="text"
        placeholder="店舗名・ブランド名・地域名で検索（例：ドラスタ、BOX、定額、KURO、メルカリ）"
    >

    <div class="filter-group">
        <div class="filter-title">買取タイプで絞る</div>
        <div class="filter-buttons">
            <button class="filter-button active" data-filter-type="source" data-filter-value="all" onclick="setFilter('source', 'all')">すべて</button>
"""

    for source_type, meta in TYPE_META.items():
        html_doc += f"""
            <button class="filter-button" data-filter-type="source" data-filter-value="{source_type}" onclick="setFilter('source', '{source_type}')">{meta["label"]}</button>
"""

    html_doc += """
        </div>
    </div>

    <div class="filter-group">
        <div class="filter-title">地域で絞る</div>
        <div class="filter-buttons">
            <button class="filter-button active" data-filter-type="area" data-filter-value="all" onclick="setFilter('area', 'all')">すべて</button>
"""

    for area in get_unique_areas():
        html_doc += f"""
            <button class="filter-button" data-filter-type="area" data-filter-value="{area["area_id"]}" onclick="setFilter('area', '{area["area_id"]}')">{area["area"]}</button>
"""

    html_doc += """
        </div>
    </div>

    <div class="filter-group">
        <div class="filter-title">ブランドで絞る</div>
        <div class="filter-buttons">
            <button class="filter-button active" data-filter-type="brand" data-filter-value="all" onclick="setFilter('brand', 'all')">すべて</button>
"""

    for brand in get_unique_brands():
        html_doc += f"""
            <button class="filter-button" data-filter-type="brand" data-filter-value="{brand["brand_id"]}" onclick="setFilter('brand', '{brand["brand_id"]}')">{brand["brand"]}</button>
"""

    html_doc += """
        </div>
    </div>

    <button class="reset-button" onclick="resetFilters()">条件をリセット</button>

    <div class="filter-status">
        表示中：<span id="visibleCount">0</span>件
    </div>
</section>
"""
    return html_doc


updated_at = datetime.now().strftime("%Y/%m/%d %H:%M")
all_posts_data = []

html_doc = build_html_start(updated_at)

for source_type, meta in TYPE_META.items():
    html_doc += f'<a href="#{source_type}">{meta["label"]}</a>\n'

html_doc += """
    </div>
</nav>

<main>

<section class="panel">
    <h2>ポケカ買取情報を、目的別にまとめてチェック</h2>
    <p>
        CardRadarは、カードショップのX投稿や公式買取表、相場確認リンクをまとめたポケカ買取情報サイトです。
        掲載情報は各店舗の投稿・公式ページを元にしています。実際の買取価格・条件・在庫状況は必ず各店舗の最新投稿や公式ページをご確認ください。
    </p>
    <div class="notice">
        X投稿はXの埋め込み機能を利用しています。画像URLはOCR準備用としてdata.jsonに保存しますが、サイト上では画像を再配布しません。
        メルカリは相場確認用の検索リンクのみ掲載し、商品情報・価格・画像の自動取得は行いません。
    </div>
</section>
"""

html_doc += render_filter_box()


with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        user_data_dir=USER_DATA_DIR,
        headless=False
    )

    page = browser.new_page()

    for source_type, meta in TYPE_META.items():
        sources = get_sources_by_type(source_type)

        html_doc += f"""
<section class="type-section" id="{source_type}">
    <div class="section-title">
        <h2>{meta["label"]}</h2>
        <p>{meta["description"]}</p>
    </div>

    <div class="source-grid">
"""

        for source in sources:
            print("==============")
            print(source["name"])
            print("==============")

            safe_description = html_lib.escape(source["description"])
            search_text = html_lib.escape(make_search_text(source))
            type_label = source_badge(source["source_type"])

            if source["source_type"] in ["online_price_list", "market_price_link"]:
                data_item = {
                    "source_type": source["source_type"],
                    "buy_type_label": TYPE_META[source["source_type"]]["label"],
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

                html_doc += f"""
        <article
            class="source-card"
            data-area="{source["area_id"]}"
            data-brand="{source["brand_id"]}"
            data-source="{source["source_type"]}"
            data-search="{search_text}"
        >
            <div class="source-head">
                <div class="source-main">
                    <div class="source-icon" style="background:{source["color"]};">{source["icon"]}</div>
                    <div>
                        <div class="label-row">
                            {type_label}
                            <span class="area-badge">{source["area"]}</span>
                            <span class="brand-badge">{source["brand"]}</span>
                        </div>
                        <h3>{source["name"]}</h3>
                        <p class="source-description">{safe_description}</p>
                    </div>
                </div>
                <div class="count">リンク</div>
            </div>

            <div class="online-card">
                <p>{safe_description}</p>
                <a class="online-button" href="{source["official_url"]}" target="_blank" rel="noopener noreferrer">ページを開く</a>
            </div>
        </article>
"""
                continue

            posts = []
            seen_urls = set()
            candidate_posts = []

            try:
                fetch_config = get_fetch_config(source)

                page.goto(source["url"], wait_until="domcontentloaded", timeout=60000)
                load_search_results(page, fetch_config)

                tweets = page.locator("article")
                count = tweets.count()
                check_limit = fetch_config["check_tweets"]

                print("検出article数:", count)
                print("チェック上限:", check_limit)

                for i in range(min(count, check_limit)):
                    tweet = tweets.nth(i)

                    url = get_status_url(tweet)

                    if not url:
                        continue

                    if url in seen_urls:
                        continue

                    text = tweet.inner_text()

                    if not is_target_post(text, source["source_type"]):
                        print("除外:", url)
                        continue

                    image_urls = get_image_urls(tweet)

                    if not image_urls and fetch_config["images_only"]:
                        print("画像なし除外:", url)
                        continue

                    summary = clean_tweet_text(text)
                    seen_urls.add(url)

                    post = {
                        "source_type": source["source_type"],
                        "buy_type_label": TYPE_META[source["source_type"]]["label"],
                        "shop_name": source["name"],
                        "shop_id": source["id"],
                        "shop_short": source["short"],
                        "area": source["area"],
                        "area_id": source["area_id"],
                        "prefecture": source["prefecture"],
                        "brand": source["brand"],
                        "brand_id": source["brand_id"],
                        "game": source["game"],
                        "tweet_url": url,
                        "status_id": get_status_id(url),
                        "summary": summary,
                        "image_urls": image_urls,
                        "image_count": len(image_urls),
                        "collected_at": updated_at,
                    }

                    candidate_posts.append(post)

                candidate_posts.sort(key=lambda x: x["status_id"], reverse=True)
                posts = candidate_posts[:MAX_TWEETS_PER_SOURCE]

                for post in posts:
                    all_posts_data.append(post)
                    print("採用:", post["tweet_url"])
                    print("画像数:", post["image_count"])

            except Exception as e:
                print("取得エラー:", e)

            html_doc += f"""
        <article
            class="source-card"
            data-area="{source["area_id"]}"
            data-brand="{source["brand_id"]}"
            data-source="{source["source_type"]}"
            data-search="{search_text}"
        >
            <div class="source-head">
                <div class="source-main">
                    <div class="source-icon" style="background:{source["color"]};">{source["icon"]}</div>
                    <div>
                        <div class="label-row">
                            {type_label}
                            <span class="area-badge">{source["area"]}</span>
                            <span class="brand-badge">{source["brand"]}</span>
                        </div>
                        <h3>{source["name"]}</h3>
                        <p class="source-description">{safe_description}</p>
                    </div>
                </div>
                <div class="count">最新{len(posts)}件</div>
            </div>

            <div class="post-list">
"""

            if posts:
                for post in posts:
                    safe_summary = html_lib.escape(post["summary"])

                    html_doc += f"""
                <div class="post-card">
                    <div class="post-summary-title">
                        <span class="hot">買取情報</span>
                        <span class="image-count">画像{post["image_count"]}枚</span>
                    </div>
                    <p>{safe_summary}</p>

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
    </div>
</section>
"""

    html_doc += """
<section class="cta-box">
    <h2>掲載店舗・買取表情報を募集中</h2>
    <p>
        CardRadarでは、ポケカ買取表を定期的に投稿しているカードショップや、オンライン買取表を掲載しているサービスを順次追加予定です。
        今後は日本橋・秋葉原・大須などの地域別ページ、カード名検索、買取価格比較、更新通知にも対応していきます。
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
    
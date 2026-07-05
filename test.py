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

DATA_RETENTION_DAYS = 30
MAX_SAVED_POSTS_PER_SOURCE = 30
STORE_VIEW_DEFAULT_DAYS = 7
STORE_VIEW_EXPANDED_DAYS = 30
STORE_VIEW_FALLBACK_POSTS = 3
SAFETY_POSTS_PER_SOURCE = MAX_SAVED_POSTS_PER_SOURCE
FALLBACK_POSTS_PER_SOURCE = 5
CHECK_POSTS_PER_SOURCE = 60
MIN_LATEST_DAY_POSTS = 8
MAX_TIMELINE_POSTS = 30
TIMELINE_FALLBACK_DAYS = 7
STORE_VIEW_RANGE_DAYS = STORE_VIEW_DEFAULT_DAYS
MAX_STORE_VIEW_POSTS_PER_SHOP = 30


# =========================
# 買取タイプ
# =========================

TYPE_ORDER = [
    "x_post_single",
    "x_post_box",
    "x_post_fixed",
    "x_post_psa",
    "x_post_other",
    "official_price_list",
    "market_price_link",
]

MAIN_FILTER_TYPES = [
    "x_post_single",
    "x_post_box",
    "x_post_fixed",
    "x_post_psa",
    "x_post_other",
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
    "x_post_other": {
        "label": "その他買取",
        "en": "OTHER",
        "desc": "サプライ・周辺グッズなどの買取",
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
ART_CARD_WORDS = "(ポケカ OR ポケモンカード OR Pokemon OR 買取表 OR 買取リスト OR 買取価格 OR 強化買取 OR 高価買取 OR 買取募集) (買取 OR 買取表 OR 買取リスト OR 買取価格 OR 強化買取 OR 高価買取 OR 募集)"
ADRENALINE_WORDS = "(ポケカ OR ポケモンカード OR Pokemon OR 買取表 OR 買取価格 OR 高価買取 OR 強化買取) (買取 OR 買取表 OR 買取価格 OR 高価買取 OR 強化買取 OR 募集)"
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

    # 日本橋・なんば周辺の追加店舗
    {
        "id": "preyz-nihonbashi-honten-single",
        "source_type": "x_post_single",
        "shop_name": "プレイズ 日本橋本店",
        "shop_slug": "preyz-nihonbashi-honten",
        "brand": "プレイズ",
        "brand_id": "preyz",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "プレイズ 日本橋本店のポケカ買取情報。",
        "url": x_search_url("Preyz_N_honten", SINGLE_WORDS),
    },
    {
        "id": "preyz-otaroad-single",
        "source_type": "x_post_single",
        "shop_name": "プレイズ オタロード店",
        "shop_slug": "preyz-otaroad",
        "brand": "プレイズ",
        "brand_id": "preyz",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "プレイズ オタロード店のポケカ買取情報。",
        "url": x_search_url("Preyz_otaroad", SINGLE_WORDS),
    },
    {
        "id": "art-card-single",
        "source_type": "x_post_single",
        "shop_name": "カードショップあーと",
        "shop_slug": "cardshop-art",
        "brand": "カードショップあーと",
        "brand_id": "art-card",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "カードショップあーとのポケカ買取情報。",
        "url": x_search_url("art_card_", ART_CARD_WORDS),
    },
    {
        "id": "cardbox-nihonbashi-single",
        "source_type": "x_post_single",
        "shop_name": "カードボックス 日本橋店",
        "shop_slug": "cardbox-nihonbashi",
        "brand": "カードボックス",
        "brand_id": "cardbox",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "カードボックス 日本橋店のポケカ買取情報。",
        "url": x_search_url("Cardbox_Japan", SINGLE_WORDS),
    },
    {
        "id": "magi-otaroad-single",
        "source_type": "x_post_single",
        "shop_name": "magi オタロード店",
        "shop_slug": "magi-otaroad",
        "brand": "magi",
        "brand_id": "magi",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "magi オタロード店のポケカ買取情報。",
        "url": x_search_url("magi_otaroad", SINGLE_WORDS),
    },
    {
        "id": "magi-nihonbashi-single",
        "source_type": "x_post_single",
        "shop_name": "magi 日本橋店",
        "shop_slug": "magi-nihonbashi",
        "brand": "magi",
        "brand_id": "magi",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "magi 日本橋店のポケカ買取情報。",
        "url": x_search_url("magiNipponbashi", SINGLE_WORDS),
    },
    {
        "id": "fullcomp-nihonbashi-single",
        "source_type": "x_post_single",
        "shop_name": "フルコンプ 日本橋店",
        "shop_slug": "fullcomp-nihonbashi",
        "brand": "フルコンプ",
        "brand_id": "fullcomp",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "フルコンプ 日本橋店のポケカ買取情報。",
        "url": x_search_url("fc_nipponbashi", SINGLE_WORDS),
    },
    {
        "id": "sunrise-cardshop-single",
        "source_type": "x_post_single",
        "shop_name": "サンライズカードショップ",
        "shop_slug": "sunrise-cardshop",
        "brand": "サンライズカードショップ",
        "brand_id": "sunrise-cardshop",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "サンライズカードショップのポケカ買取情報。",
        "url": x_search_url("SunriseCardshop", SINGLE_WORDS),
    },
    {
        "id": "adrenaline-single",
        "source_type": "x_post_single",
        "shop_name": "アドレナリン",
        "shop_slug": "adrenaline",
        "brand": "アドレナリン",
        "brand_id": "adrenaline",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "アドレナリンのポケカ買取情報。",
        "url": x_search_url("Ado_renalinemax", ADRENALINE_WORDS),
    },
    {
        "id": "treca-champion-single",
        "source_type": "x_post_single",
        "shop_name": "トレカチャンピオン",
        "shop_slug": "treca-champion",
        "brand": "トレカチャンピオン",
        "brand_id": "treca-champion",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "トレカチャンピオンのポケカ買取情報。",
        "url": x_search_url("TC_nanba", SINGLE_WORDS),
    },
    {
        "id": "kaitori-champion-single",
        "source_type": "x_post_single",
        "shop_name": "買取チャンピオン",
        "shop_slug": "kaitori-champion",
        "brand": "買取チャンピオン",
        "brand_id": "kaitori-champion",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "買取チャンピオンのポケカ買取情報。",
        "url": x_search_url("chanpion2877", SINGLE_WORDS),
    },
    {
        "id": "kaitori-v-single",
        "source_type": "x_post_single",
        "shop_name": "買取V",
        "shop_slug": "kaitori-v",
        "brand": "買取V",
        "brand_id": "kaitori-v",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "買取Vのポケカ買取情報。",
        "url": x_search_url("vshacho", SINGLE_WORDS),
    },
    {
        "id": "tonton-osaka-nihonbashi-single",
        "source_type": "x_post_single",
        "shop_name": "カードショップとんとん大阪日本橋店",
        "shop_slug": "tonton-osaka-nihonbashi",
        "brand": "カードショップとんとん",
        "brand_id": "tonton",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "カードショップとんとん大阪日本橋店のポケカ買取情報。",
        "url": x_search_url("tontontcg_osaka", SINGLE_WORDS),
    },
    {
        "id": "hiki-card-osaka-single",
        "source_type": "x_post_single",
        "shop_name": "トレカショップ 比希商店",
        "shop_slug": "hiki-card-osaka",
        "brand": "比希商店",
        "brand_id": "hiki-card",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "トレカショップ 比希商店のポケカ買取情報。",
        "url": x_search_url("hikicardosaka", SINGLE_WORDS),
    },
    {
        "id": "lotus-osaka-nihonbashi-single",
        "source_type": "x_post_single",
        "shop_name": "Lotus 大阪日本橋店",
        "shop_slug": "lotus-osaka-nihonbashi",
        "brand": "Lotus",
        "brand_id": "lotus",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "Lotus 大阪日本橋店のポケカ買取情報。",
        "url": x_search_url("Lotus_osakaten", SINGLE_WORDS),
    },
    {
        "id": "torecaline-otaroad-single",
        "source_type": "x_post_single",
        "shop_name": "トレカライン オタロード店",
        "shop_slug": "torecaline-otaroad",
        "brand": "トレカライン",
        "brand_id": "torecaline",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "トレカライン オタロード店のポケカ買取情報。",
        "url": x_search_url("torecaline2", SINGLE_WORDS),
    },
    {
        "id": "torecaline-namba-ekimae-single",
        "source_type": "x_post_single",
        "shop_name": "トレカライン 難波駅前店",
        "shop_slug": "torecaline-namba-ekimae",
        "brand": "トレカライン",
        "brand_id": "torecaline",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "トレカライン 難波駅前店のポケカ買取情報。",
        "url": x_search_url("torecaline1", SINGLE_WORDS),
    },
    {
        "id": "toreka-douraku-single",
        "source_type": "x_post_single",
        "shop_name": "トレカ道楽",
        "shop_slug": "toreka-douraku",
        "brand": "トレカ道楽",
        "brand_id": "toreka-douraku",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "トレカ道楽のポケカ買取情報。",
        "url": x_search_url("Torekadouraku", SINGLE_WORDS),
    },
    {
        "id": "toreca-bomb-single",
        "source_type": "x_post_single",
        "shop_name": "トレカボム",
        "shop_slug": "toreca-bomb",
        "brand": "トレカボム",
        "brand_id": "toreca-bomb",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "トレカボムのポケカ買取情報。",
        "url": x_search_url("torecabomb", SINGLE_WORDS),
    },

    # 公式Web買取表

    # Additional Nipponbashi candidate stores (temporary display names)
    {
        "id": "hbstnipponbashi-single",
        "source_type": "x_post_single",
        "shop_name": "ホビーステーション日本橋店",
        "shop_slug": "hbstnipponbashi",
        "brand": "ホビーステーション日本橋店",
        "brand_id": "hbstnipponbashi",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "ホビーステーション日本橋店 のポケカ買取情報。",
        "url": x_search_url("hbstnipponbashi", SINGLE_WORDS),
    },
    {
        "id": "fullaheadosaka-single",
        "source_type": "x_post_single",
        "shop_name": "フルアヘッド大阪日本橋店",
        "shop_slug": "fullaheadosaka",
        "brand": "フルアヘッド大阪日本橋店",
        "brand_id": "fullaheadosaka",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "フルアヘッド大阪日本橋店 のポケカ買取情報。",
        "url": x_search_url("fullaheadosaka", SINGLE_WORDS),
    },
    {
        "id": "pozcket-ptc-single",
        "source_type": "x_post_single",
        "shop_name": "ポズケット",
        "shop_slug": "pozcket-ptc",
        "brand": "ポズケット",
        "brand_id": "pozcket-ptc",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "ポズケット のポケカ買取情報。",
        "url": x_search_url("pozcket_ptc", SINGLE_WORDS),
    },
    {
        "id": "ninnin-osaka-single",
        "source_type": "x_post_single",
        "shop_name": "ニンニン大阪日本橋店",
        "shop_slug": "ninnin-osaka",
        "brand": "ニンニン大阪日本橋店",
        "brand_id": "ninnin-osaka",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "ニンニン大阪日本橋店 のポケカ買取情報。",
        "url": x_search_url("ninnin_osaka", SINGLE_WORDS),
    },
    {
        "id": "toreca-pike-single",
        "source_type": "x_post_single",
        "shop_name": "トレカパイク",
        "shop_slug": "toreca-pike",
        "brand": "トレカパイク",
        "brand_id": "toreca-pike",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "トレカパイク のポケカ買取情報。",
        "url": x_search_url("toreca_pike", SINGLE_WORDS),
    },
    {
        "id": "clever-osaka-single",
        "source_type": "x_post_single",
        "shop_name": "CLEVER 日本橋店オタロード",
        "shop_slug": "clever-osaka",
        "brand": "CLEVER 日本橋店オタロード",
        "brand_id": "clever-osaka",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "CLEVER 日本橋店オタロード のポケカ買取情報。",
        "url": x_search_url("clever_osaka", SINGLE_WORDS),
    },
    {
        "id": "cardstock-kt-single",
        "source_type": "x_post_single",
        "shop_name": "CARD STOCK",
        "shop_slug": "cardstock-kt",
        "brand": "CARD STOCK",
        "brand_id": "cardstock-kt",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "CARD STOCK のポケカ買取情報。",
        "url": x_search_url("cardstock_kt", SINGLE_WORDS),
    },
    {
        "id": "card-daburea-single",
        "source_type": "x_post_single",
        "shop_name": "カードショップ だぶれあ",
        "shop_slug": "card-daburea",
        "brand": "カードショップ だぶれあ",
        "brand_id": "card-daburea",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "カードショップ だぶれあ のポケカ買取情報。",
        "url": x_search_url("card_daburea", SINGLE_WORDS),
    },
    {
        "id": "oldcard-topsun-single",
        "source_type": "x_post_single",
        "shop_name": "TOP SUN",
        "shop_slug": "oldcard-topsun",
        "brand": "TOP SUN",
        "brand_id": "oldcard-topsun",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "TOP SUN のポケカ買取情報。",
        "url": x_search_url("oldcard_topsun", SINGLE_WORDS),
    },
    {
        "id": "card-shop-n-single",
        "source_type": "x_post_single",
        "shop_name": "カードショップN",
        "shop_slug": "card-shop-n",
        "brand": "カードショップN",
        "brand_id": "card-shop-n",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "カードショップN のポケカ買取情報。",
        "url": x_search_url("card_shop_n", SINGLE_WORDS),
    },
    {
        "id": "kaitori-k1-single",
        "source_type": "x_post_single",
        "shop_name": "買取K1",
        "shop_slug": "kaitori-k1",
        "brand": "買取K1",
        "brand_id": "kaitori-k1",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "買取K1 のポケカ買取情報。",
        "url": x_search_url("kaitori_k1", SINGLE_WORDS),
    },
    {
        "id": "baseclovenamba-single",
        "source_type": "x_post_single",
        "shop_name": "Clove Base なんば",
        "shop_slug": "baseclovenamba",
        "brand": "Clove Base なんば",
        "brand_id": "baseclovenamba",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "Clove Base なんば のポケカ買取情報。",
        "url": x_search_url("baseclovenamba", SINGLE_WORDS),
    },
    {
        "id": "cardshop-allium-single",
        "source_type": "x_post_single",
        "shop_name": "カードショップAllium",
        "shop_slug": "cardshop-allium",
        "brand": "カードショップAllium",
        "brand_id": "cardshop-allium",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "カードショップAllium のポケカ買取情報。",
        "url": x_search_url("cardshop_allium", SINGLE_WORDS),
    },
    {
        "id": "torekayajin-single",
        "source_type": "x_post_single",
        "shop_name": "トレカ屋仁",
        "shop_slug": "torekayajin",
        "brand": "トレカ屋仁",
        "brand_id": "torekayajin",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "トレカ屋仁 のポケカ買取情報。",
        "url": x_search_url("torekayajin", SINGLE_WORDS),
    },
    {
        "id": "torecamaison-single",
        "source_type": "x_post_single",
        "shop_name": "トレカメゾン",
        "shop_slug": "torecamaison",
        "brand": "トレカメゾン",
        "brand_id": "torecamaison",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "トレカメゾン のポケカ買取情報。",
        "url": x_search_url("torecamaison", SINGLE_WORDS),
    },
    {
        "id": "meets-tcg-osaka-single",
        "source_type": "x_post_single",
        "shop_name": "MEETS TCG 大阪",
        "shop_slug": "meets-tcg-osaka",
        "brand": "MEETS TCG 大阪",
        "brand_id": "meets-tcg-osaka",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "MEETS TCG 大阪 のポケカ買取情報。",
        "url": x_search_url("meets_tcg_osaka", SINGLE_WORDS),
    },
    {
        "id": "kirin250428-single",
        "source_type": "x_post_single",
        "shop_name": "鑑定屋きりん",
        "shop_slug": "kirin250428",
        "brand": "鑑定屋きりん",
        "brand_id": "kirin250428",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "鑑定屋きりん のポケカ買取情報。",
        "url": x_search_url("kirin250428", SINGLE_WORDS),
    },
    {
        "id": "cardshop-nest15-single",
        "source_type": "x_post_single",
        "shop_name": "カードショップNEST",
        "shop_slug": "cardshop-nest15",
        "brand": "カードショップNEST",
        "brand_id": "cardshop-nest15",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "カードショップNEST のポケカ買取情報。",
        "url": x_search_url("cardshop_nest15", SINGLE_WORDS),
    },
    {
        "id": "supportchance-single",
        "source_type": "x_post_single",
        "shop_name": "サポートチャンス",
        "shop_slug": "supportchance",
        "brand": "サポートチャンス",
        "brand_id": "supportchance",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "サポートチャンス のポケカ買取情報。",
        "url": x_search_url("supportchance_", SINGLE_WORDS),
    },
    {
        "id": "poem-pokeca-single",
        "source_type": "x_post_single",
        "shop_name": "POEM ポケカ",
        "shop_slug": "poem-pokeca",
        "brand": "POEM ポケカ",
        "brand_id": "poem-pokeca",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "POEM ポケカ のポケカ買取情報。",
        "url": x_search_url("poem_pokeca", SINGLE_WORDS),
    },
    {
        "id": "torekanain-single",
        "source_type": "x_post_single",
        "shop_name": "トレカナイン",
        "shop_slug": "torekanain",
        "brand": "トレカナイン",
        "brand_id": "torekanain",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "トレカナイン のポケカ買取情報。",
        "url": x_search_url("torekanain", SINGLE_WORDS),
    },
    {
        "id": "dream-osaka-single",
        "source_type": "x_post_single",
        "shop_name": "DREAM 大阪",
        "shop_slug": "dream-osaka",
        "brand": "DREAM 大阪",
        "brand_id": "dream-osaka",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "DREAM 大阪 のポケカ買取情報。",
        "url": x_search_url("dream_osaka_", SINGLE_WORDS),
    },
    {
        "id": "tcg-torejaras-single",
        "source_type": "x_post_single",
        "shop_name": "TCGトレジャラス",
        "shop_slug": "tcg-torejaras",
        "brand": "TCGトレジャラス",
        "brand_id": "tcg-torejaras",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "TCGトレジャラス のポケカ買取情報。",
        "url": x_search_url("tcg_torejaras", SINGLE_WORDS),
    },
    {
        "id": "kaitorigorira2-single",
        "source_type": "x_post_single",
        "shop_name": "買取ゴリラ2",
        "shop_slug": "kaitorigorira2",
        "brand": "買取ゴリラ2",
        "brand_id": "kaitorigorira2",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "買取ゴリラ2 のポケカ買取情報。",
        "url": x_search_url("kaitorigorira2", SINGLE_WORDS),
    },
    {
        "id": "bar-unknown-single",
        "source_type": "x_post_single",
        "shop_name": "BAR UNKNOWN",
        "shop_slug": "bar-unknown",
        "brand": "BAR UNKNOWN",
        "brand_id": "bar-unknown",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "BAR UNKNOWN のポケカ買取情報。",
        "url": x_search_url("bar_unknown", SINGLE_WORDS),
    },
    {
        "id": "osaka-193tcg-single",
        "source_type": "x_post_single",
        "shop_name": "193 大阪日本橋店",
        "shop_slug": "osaka-193tcg",
        "brand": "193 大阪日本橋店",
        "brand_id": "osaka-193tcg",
        "area": "大阪・日本橋",
        "area_id": "osaka-nihonbashi",
        "description": "193 大阪日本橋店 のポケカ買取情報。",
        "url": x_search_url("osaka_193tcg", SINGLE_WORDS),
    },

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


SHOP_DISPLAY_ORDER = [
    "dragonstar-nihonbashi-honten",
    "dragonstar-nihonbashi-2",
    "dragonstar-nihonbashi-3",
    "dragonstar-otaroad-chuo",
    "dragonstar-nansan",
    "cardlabo-namba",
    "cardlabo-osaka-nihonbashi",
    "girafull-namba",
    "girafull-osaka-nihonbashi",
    "girafull-otaroad",
    "magi-nihonbashi",
    "magi-otaroad",
    "preyz-nihonbashi-honten",
    "preyz-otaroad",
    "hareruya2-namba",
    "fullcomp-nihonbashi",
    "cardbox-nihonbashi",
]


def sort_shops_for_display(shops):
    order = {shop_slug: index for index, shop_slug in enumerate(SHOP_DISPLAY_ORDER)}
    original_order = {shop["shop_slug"]: index for index, shop in enumerate(shops)}
    return sorted(
        shops,
        key=lambda shop: (
            order.get(shop["shop_slug"], len(SHOP_DISPLAY_ORDER)),
            original_order.get(shop["shop_slug"], len(shops)),
        ),
    )


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


STRONG_BUYLIST_WORDS = [
    "買取表",
    "買取リスト",
    "買取価格",
    "買取保証",
    "強化買取",
    "買取強化",
    "高価買取",
    "買取更新",
    "買取情報",
    "シングル買取",
    "シングルカード買取",
    "定額買取",
    "定額保証",
    "保証買取",
    "BOX買取",
    "パック買取",
    "カートン買取",
    "サプライ買取",
    "グッズ買取",
    "ポケカ買取",
    "ポケモンカード買取",
    "WANTED",
    "募集",
    "最低保証",
    "定額",
    "一律",
    "まとめ買取",
    "PSA買取",
    "BOX買取",
]

NON_BUYLIST_NOTICE_WORDS = [
    "営業時間",
    "営業案内",
    "営業時間案内",
    "営業日",
    "休業",
    "臨時休業",
    "定休日",
    "開店",
    "閉店",
    "本日の営業時間",
    "年末年始",
    "棚卸",
    "買取時間",
    "買取受付時間",
    "受付時間",
    "本日営業",
    "店舗案内",
    "お知らせ",
]

NON_BUYLIST_SALES_WORDS = [
    "販売",
    "販売中",
    "販売開始",
    "販売情報",
    "販売価格",
    "入荷",
    "入荷情報",
    "再入荷",
    "在庫",
    "在庫情報",
    "特価",
    "セール",
    "キャンペーン",
    "オリパ",
    "ガチャ",
    "くじ",
    "抽選販売",
    "大会",
    "イベント",
    "抽選",
    "予約",
    "受付中",
    "発売",
    "店頭販売",
    "購入",
    "ご購入",
    "完売",
]

NON_BUYLIST_AFTER_BUY_WORDS = [
    "買取しました",
    "買取させていただきました",
    "買取させて頂きました",
    "買い取らせていただきました",
    "お買取り",
    "お買取",
    "買取ありがとうございます",
    "買取ありがとうございました",
    "買取実績",
    "買取成立",
    "買取後",
    "買取完了",
    "お売りいただき",
    "お売りいただきました",
    "お売り頂き",
    "お売り頂きました",
    "お持ち込み",
    "ご来店ありがとうございました",
]

HARD_NON_BUYLIST_WORDS = [
    "本日の営業は終了しました",
    "営業は終了しました",
    "買取停止中",
    "トレカ買取停止中",
    "高額PSA売るなら",
    "PSA売るなら",
    "全額現金払出し",
]

ART_STORE_SALES_WORDS = [
    "販売",
    "販売中",
    "販売開始",
    "販売情報",
    "販売価格",
    "入荷",
    "入荷情報",
    "再入荷",
    "在庫",
    "在庫情報",
    "特価",
    "セール",
    "オリパ",
    "サプライ",
    "完売",
    "購入",
    "ご購入",
    "抽選販売",
    "予約",
    "発売",
]

ART_STORE_STRONG_BUYLIST_WORDS = [
    "買取表",
    "買取リスト",
    "買取価格",
    "買取保証",
    "強化買取",
    "買取強化",
    "買取更新",
    "ポケカ買取",
    "ポケモンカード買取",
    "高価買取",
    "買取募集",
]

LOTUS_NOTICE_WORDS = [
    "営業時間",
    "営業案内",
    "営業時間案内",
    "本日の営業時間",
    "営業時間のお知らせ",
    "営業中",
    "開店",
    "閉店",
    "本日営業",
    "店舗案内",
    "お知らせ",
    "買取時間",
    "買取受付時間",
    "買取受付",
    "受付時間",
    "延長営業",
]

STRICT_BUYLIST_SHOP_SLUGS = {
    "tonton-osaka-nihonbashi",
}


def has_strong_buylist_signal(text):
    return contains_any(text, STRONG_BUYLIST_WORDS)


def is_non_buylist_text(text):
    if contains_any(text, HARD_NON_BUYLIST_WORDS):
        return True
    if has_strong_buylist_signal(text):
        return False
    return contains_any(
        text,
        NON_BUYLIST_NOTICE_WORDS + NON_BUYLIST_SALES_WORDS + NON_BUYLIST_AFTER_BUY_WORDS,
    )


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
        "買取リスト",
        "買取価格",
        "WANTED",
        "募集",
        "取扱強化",
        "買取情報",
        "シングル買取",
        "シングルカード買取",
        "定額買取",
        "定額保証",
        "保証買取",
        "BOX買取",
        "パック買取",
        "カートン買取",
        "サプライ買取",
        "グッズ買取",
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

    if contains_any(text, HARD_NON_BUYLIST_WORDS):
        return False

    if not contains_any(text, pokemon_words):
        return False

    if not contains_any(text, buy_words):
        return False

    return not is_non_buylist_text(text)


def target_exclusion_reason(text):
    pokemon_words = ["ポケカ", "ポケモンカード", "ポケモンカードゲーム", "Pokemon", "pokemon"]
    buy_words = [
        "買取", "高価買取", "買取表", "買取リスト", "買取価格", "WANTED",
        "募集", "買取強化", "買取情報", "シングル買取", "シングルカード買取",
        "定額買取", "定額保証", "保証買取", "BOX買取", "パック買取",
        "カートン買取", "サプライ買取", "グッズ買取",
    ]
    ng_words = [
        "大会", "優勝", "抽選", "販売開始", "BOX争奪戦", "争奪戦",
        "ワンピース", "遊戯王", "デュエマ", "MTG", "ヴァイス",
        "バトスピ", "ドラゴンボール",
    ]
    if contains_any(text, ng_words):
        return "NGワード"
    if contains_any(text, HARD_NON_BUYLIST_WORDS):
        return "買取表ではない"
    if not contains_any(text, pokemon_words):
        return "ポケカ外"
    if not contains_any(text, buy_words):
        return "買取表ではない"
    if is_non_buylist_text(text):
        return "お知らせ系"
    return "買取表ではない"


def is_art_store_target_post(text):
    if contains_any(text, ART_STORE_STRONG_BUYLIST_WORDS):
        return True
    if contains_any(text, ART_STORE_SALES_WORDS):
        return False
    return is_target_post(text, "x_post_single")


def is_strict_shop_non_buylist_post(post):
    if post.get("shop_slug") not in STRICT_BUYLIST_SHOP_SLUGS:
        return False
    text = post_content_filter_text(post)
    return not has_strong_buylist_signal(text)


def is_art_store_sales_post(post):
    if post.get("shop_slug") != "cardshop-art":
        return False
    text = post_content_filter_text(post)
    if contains_any(text, ART_STORE_STRONG_BUYLIST_WORDS):
        return False
    return contains_any(text, ART_STORE_SALES_WORDS)


def is_lotus_hours_notice_post(post):
    if post.get("shop_slug") != "lotus-osaka-nihonbashi":
        return False
    text = post_content_filter_text(post)
    if not contains_any(text, LOTUS_NOTICE_WORDS):
        return False
    if contains_any(text, ART_STORE_STRONG_BUYLIST_WORDS):
        return False
    return True


def classify_display_type(text, source_type):
    psa_words = ["PSA", "PSA10", "PSA9", "PSA 10", "PSA 9", "鑑定品", "鑑定", "ARS", "BGS", "ケース付き", "グレーディング"]
    psa_ng_words = ["PSA買取不可", "PSA対象外", "PSAは対象外", "PSA買取なし"]
    fixed_words = ["定額", "一律", "一律買取", "最低保証", "買取保証", "保証買取", "定額保証", "まとめ買取", "RR定額", "AR定額", "SR定額", "UR定額", "ノーマル買取", "ノーマル", "ストレージ", "汎用", "大量買取"]
    box_words = ["BOX", "未開封", "未開封BOX", "未開封商品", "未開封買取", "シュリンク", "シュリンク付き", "カートン", "カートン買取", "1BOX", "BOX買取", "パック", "パック買取"]
    box_ng_words = ["BOX以外", "BOX買取以外", "ボックス以外", "未開封BOX以外", "BOX対象外", "BOXは対象外", "BOX買取なし"]
    other_words = [
        "サプライ",
        "スリーブ",
        "デッキケース",
        "プレイマット",
        "ローダー",
        "マグネットローダー",
        "カードファイル",
        "バインダー",
        "ストレージボックス",
        "デッキシールド",
        "プレイヤーズグッズ",
        "周辺グッズ",
        "グッズ買取",
    ]

    if not contains_any(text, psa_ng_words):
        matches = matching_words(text, psa_words)
        if matches:
            return "x_post_psa", ",".join(matches)

    if not contains_any(text, box_ng_words):
        matches = matching_words(text, box_words)
        if matches:
            return "x_post_box", ",".join(matches)

    matches = matching_words(text, fixed_words)
    if matches:
        return "x_post_fixed", ",".join(matches)

    matches = matching_words(text, other_words)
    if matches:
        return "x_post_other", ",".join(matches)

    if source_type in TYPE_META and source_type.startswith("x_post_"):
        return source_type, "source_type fallback"

    return "x_post_single", "default single"


def classification_text_for_post(post, source=None):
    text = post.get("full_text") or post.get("summary") or ""
    remove_values = [
        "カードボックス",
        "カードボックス日本橋店",
        "CARD BOX",
        "CARDBOX",
        "Cardbox",
        "cardbox",
        "Cardbox_Japan",
        "@Cardbox_Japan",
    ]

    for data in (source or {}, post or {}):
        for key in ["shop_name", "brand", "account"]:
            value = str(data.get(key, "") or "").strip()
            if not value:
                continue
            remove_values.append(value)
            remove_values.append(value.replace(" ", "").replace("　", ""))
            if key == "account":
                remove_values.append("@" + value.lstrip("@"))

    for value in sorted(set(remove_values), key=len, reverse=True):
        if not value:
            continue
        text = re.sub(re.escape(value), " ", text, flags=re.IGNORECASE)
    return text


def display_type_label(display_type):
    return short_type_label(TYPE_META.get(display_type, TYPE_META["x_post_single"])["label"])


def display_filter_text(post):
    return " ".join([
        str(post.get("full_text", "")),
        str(post.get("text", "")),
        str(post.get("summary", "")),
        str(post.get("buy_type_label", "")),
        str(post.get("type_label", "")),
        str(post.get("display_type_label", "")),
        str(post.get("shop_name", "")),
        str(post.get("brand", "")),
    ])


def post_content_filter_text(post):
    return " ".join([
        str(post.get("full_text", "")),
        str(post.get("text", "")),
        str(post.get("summary", "")),
        str(post.get("shop_name", "")),
        str(post.get("brand", "")),
    ])


def is_non_pokemon_post(post):
    text = display_filter_text(post)

    pokemon_words = ["ポケカ", "ポケモンカード", "ポケモン", "Pokemon", "Pokémon", "ポケットモンスター"]
    non_pokemon_words = [
        "遊戯王", "遊戯王OCG", "YU-GI-OH", "ユギオウ",
        "ワンピースカード", "ONE PIECE CARD",
        "デュエマ", "デュエルマスターズ",
        "ヴァイス", "Weiss",
        "バトスピ", "バトルスピリッツ",
        "ユニオンアリーナ", "UNION ARENA",
        "ドラゴンボールカード", "DBFW",
        "ガンダム", "GUNDAM", "Gundam", "ガンプラ", "機動戦士", "機動戦士ガンダム",
    ]
    hard_non_pokemon_words = [
        # X本文に #ポケカ が混ざっていても、カード名から別TCGと分かるものだけを落とす。
        "雙王の械", "闇の眼を持つ幻想師", "トゥーンのもくじ",
        "ガンダム", "GUNDAM", "Gundam", "ガンプラ", "機動戦士", "機動戦士ガンダム",
    ]

    if contains_any(text, hard_non_pokemon_words):
        return True
    if contains_any(text, pokemon_words):
        return False
    return contains_any(text, non_pokemon_words)


def is_non_buy_notice_post(post):
    text = post_content_filter_text(post)
    if is_art_store_sales_post(post):
        return True
    if is_lotus_hours_notice_post(post):
        return True
    if is_strict_shop_non_buylist_post(post):
        return True
    return is_non_buylist_text(text)


def filter_display_posts(posts):
    return [
        post for post in posts
        if not is_non_pokemon_post(post) and not is_non_buy_notice_post(post)
    ]


def count_non_pokemon_exclusions(posts_by_source):
    excluded_keys = set()
    for source_posts in posts_by_source.values():
        for raw_post in source_posts:
            post = normalize_post(raw_post)
            if not is_non_pokemon_post(post):
                continue
            key = post.get("tweet_url") or post.get("status_id") or id(raw_post)
            excluded_keys.add(key)
    return len(excluded_keys)


def count_notice_exclusions(posts_by_source):
    excluded_keys = set()
    for source_posts in posts_by_source.values():
        for raw_post in source_posts:
            post = normalize_post(raw_post)
            if is_non_pokemon_post(post) or not is_non_buy_notice_post(post):
                continue
            key = post.get("tweet_url") or post.get("status_id") or id(raw_post)
            excluded_keys.add(key)
    return len(excluded_keys)


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
    text_for_class = classification_text_for_post(post, source)
    display_type, reason = classify_display_type(text_for_class, source_type)
    post["display_type"] = display_type
    post["display_type_label"] = display_type_label(post["display_type"])
    post["buy_type_label"] = post.get("buy_type_label") or TYPE_META.get(source_type, TYPE_META["x_post_single"])["label"]
    post["posted_at"] = post.get("posted_at") or ""
    post["posted_date_jst"] = post.get("posted_date_jst") or posted_date_from_values(post.get("posted_at"), post.get("collected_at"))
    post["classify_reason"] = reason
    post["image_urls"] = post.get("image_urls") or []
    post["image_count"] = len(post["image_urls"])
    post["status_id"] = post.get("status_id") or get_status_id(post.get("tweet_url", ""))
    return post


def select_latest_posts(candidates):
    candidates = [normalize_post(post) for post in candidates]
    candidates.sort(key=sort_post_key, reverse=True)
    posted_candidates = [post for post in candidates if parse_jst_date(post.get("posted_date_jst"))]
    if posted_candidates:
        latest_date_obj = max(parse_jst_date(post["posted_date_jst"]) for post in posted_candidates)
        retained_posts = []
        for post in candidates:
            post_date = parse_jst_date(post.get("posted_date_jst"))
            if not post_date:
                continue
            days_old = (latest_date_obj - post_date).days
            if 0 <= days_old < DATA_RETENTION_DAYS:
                retained_posts.append(post)
        return retained_posts[:MAX_SAVED_POSTS_PER_SOURCE]
    return candidates[:FALLBACK_POSTS_PER_SOURCE]


def build_source_selection_log(candidates, posts):
    dated_candidates = [post for post in candidates if parse_jst_date(post.get("posted_date_jst"))]
    latest_date = "-"
    retention_saved = "なし"
    if dated_candidates:
        latest_date_obj = max(parse_jst_date(post["posted_date_jst"]) for post in dated_candidates)
        latest_date = latest_date_obj.strftime("%Y-%m-%d")
        retention_saved = "あり"
    return (
        f"取得候補：{len(candidates)}件 / "
        f"保存対象：{len(posts)}件 / "
        f"最新日：{latest_date} / "
        f"過去{DATA_RETENTION_DAYS}日保存：{retention_saved}"
    )


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

    posts = filter_display_posts(posts)
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


def merge_posts_by_tweet(posts):
    posts_by_key = {}

    for raw_post in posts:
        post = normalize_post(raw_post)
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

    merged_posts = list(posts_by_key.values())
    merged_posts.sort(key=sort_post_key, reverse=True)
    return merged_posts

def get_timeline_posts(posts_by_source, area_id):
    posts_by_key = {}

    for source_posts in posts_by_source.values():
        for raw_post in source_posts:
            post = normalize_post(raw_post)
            if post.get("area_id") != area_id:
                continue
            if is_non_pokemon_post(post) or is_non_buy_notice_post(post):
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


def parse_jst_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def select_timeline_posts_with_fallback(posts):
    posts = [normalize_post(post) for post in posts]
    posts.sort(key=sort_post_key, reverse=True)

    meta = {
        "latest_date": "",
        "latest_count": 0,
        "fallback_used": False,
        "selected_count": 0,
    }
    if not posts:
        return [], meta

    dated_posts = [post for post in posts if post.get("posted_date_jst")]
    if not dated_posts:
        selected = posts[:MAX_TIMELINE_POSTS]
        meta["selected_count"] = len(selected)
        return selected, meta

    latest_date = max(post["posted_date_jst"] for post in dated_posts)
    latest_day_posts = [post for post in posts if post.get("posted_date_jst") == latest_date]
    meta["latest_date"] = latest_date
    meta["latest_count"] = len(latest_day_posts)

    if len(latest_day_posts) >= MIN_LATEST_DAY_POSTS:
        selected = latest_day_posts[:MAX_TIMELINE_POSTS]
        meta["selected_count"] = len(selected)
        return selected, meta

    latest_date_obj = parse_jst_date(latest_date)
    selected = list(latest_day_posts)
    seen_keys = {post.get("tweet_url") or post.get("status_id") for post in selected}

    fallback_posts = []
    for post in posts:
        key = post.get("tweet_url") or post.get("status_id")
        if key in seen_keys:
            continue
        post_date = parse_jst_date(post.get("posted_date_jst"))
        if latest_date_obj:
            if not post_date:
                continue
            days_old = (latest_date_obj - post_date).days
            if days_old <= 0 or days_old > TIMELINE_FALLBACK_DAYS:
                continue
        fallback_posts.append(post)

    selected.extend(fallback_posts[: max(0, MAX_TIMELINE_POSTS - len(selected))])
    selected.sort(key=sort_post_key, reverse=True)
    meta["fallback_used"] = len(selected) > len(latest_day_posts)
    meta["selected_count"] = len(selected)
    return selected, meta


def post_identity(post):
    return post.get("tweet_url") or post.get("status_id") or f'{post.get("source_id", "")}:{post.get("image_url", "")}'


def build_store_view_meta(mode_label, start_date, end_date, posts):
    display_types = []
    for post in posts:
        display_type = post.get("display_type", infer_display_type(post))
        if display_type not in display_types:
            display_types.append(display_type)
    type_text = " / ".join(short_type_label(t) for t in display_types) if display_types else "未分類"
    if mode_label == "最新のみ":
        date_text = format_date_label(end_date) if end_date else "未取得"
    else:
        start_text = format_date_label(start_date) if start_date else "未取得"
        end_text = format_date_label(end_date) if end_date else "未取得"
        date_text = f"{start_text}〜{end_text}" if start_text != end_text else end_text
    return f"{mode_label}：{date_text} / 投稿{len(posts)}件 / {type_text}"


def store_post_age_badge(post, reference_date):
    latest_date_obj = parse_jst_date(reference_date)
    post_date = parse_jst_date(post.get("posted_date_jst"))
    if not latest_date_obj or not post_date:
        return ""
    days_old = (latest_date_obj - post_date).days
    if days_old >= 14:
        return "14日超"
    if days_old >= STORE_VIEW_DEFAULT_DAYS:
        return "7日超"
    return ""


def select_store_view_posts(shop_posts, reference_date=None):
    posts = [normalize_post(post) for post in shop_posts]
    posts.sort(key=sort_post_key, reverse=True)
    meta = {
        "default_meta": "過去7日：未取得 / 投稿0件 / 未分類",
        "expanded_meta": "過去30日：未取得 / 投稿0件 / 未分類",
        "default_keys": set(),
        "expanded_keys": set(),
        "latest_date": "",
    }
    if not posts:
        return [], [], meta

    dated_posts = [post for post in posts if post.get("posted_date_jst")]
    if not dated_posts:
        fallback_posts = posts[:STORE_VIEW_FALLBACK_POSTS]
        expanded_posts = posts[:MAX_STORE_VIEW_POSTS_PER_SHOP]
        meta["default_meta"] = build_store_view_meta("過去7日", "", "", fallback_posts)
        meta["expanded_meta"] = build_store_view_meta("過去30日", "", "", expanded_posts)
        meta["default_keys"] = {post_identity(post) for post in fallback_posts}
        meta["expanded_keys"] = {post_identity(post) for post in expanded_posts}
        return fallback_posts, expanded_posts, meta

    latest_date = max(post["posted_date_jst"] for post in dated_posts)
    latest_date_obj = parse_jst_date(latest_date)
    reference_date_obj = parse_jst_date(reference_date) or latest_date_obj
    reference_date_text = reference_date_obj.strftime("%Y-%m-%d") if reference_date_obj else latest_date
    meta["latest_date"] = latest_date

    default_posts = []
    expanded_posts = []
    if reference_date_obj:
        for post in posts:
            post_date = parse_jst_date(post.get("posted_date_jst"))
            if not post_date:
                continue
            days_old = (reference_date_obj - post_date).days
            if 0 <= days_old < STORE_VIEW_EXPANDED_DAYS:
                expanded_posts.append(post)
    else:
        expanded_posts = posts[:MAX_STORE_VIEW_POSTS_PER_SHOP]

    expanded_posts.sort(key=sort_post_key, reverse=True)
    expanded_posts = expanded_posts[:MAX_STORE_VIEW_POSTS_PER_SHOP]
    default_posts = expanded_posts[:STORE_VIEW_FALLBACK_POSTS]

    default_start_obj = reference_date_obj - timedelta(days=STORE_VIEW_DEFAULT_DAYS - 1) if reference_date_obj else None
    expanded_start_obj = reference_date_obj - timedelta(days=STORE_VIEW_EXPANDED_DAYS - 1) if reference_date_obj else None
    default_start = default_start_obj.strftime("%Y-%m-%d") if default_start_obj else reference_date_text
    expanded_start = expanded_start_obj.strftime("%Y-%m-%d") if expanded_start_obj else reference_date_text
    meta["default_meta"] = build_store_view_meta("過去7日", default_start, reference_date_text, default_posts)
    meta["expanded_meta"] = build_store_view_meta("過去30日", expanded_start, reference_date_text, expanded_posts)
    meta["default_keys"] = {post_identity(post) for post in default_posts}
    meta["expanded_keys"] = {post_identity(post) for post in expanded_posts}
    return default_posts, expanded_posts, meta


def short_type_label(label_or_type):
    mapping = {
        "x_post_single": "シングル", "x_post_box": "BOX", "x_post_fixed": "定額", "x_post_psa": "PSA", "x_post_other": "その他",
        "official_price_list": "公式Web", "market_price_link": "相場",
        "シングル買取": "シングル", "BOX買取": "BOX", "定額買取": "定額", "PSA買取": "PSA", "その他買取": "その他",
        "公式Web買取表": "公式Web", "相場確認": "相場",
    }
    return mapping.get(label_or_type, label_or_type or "買取")


def infer_type_priority(source_type):
    order = {
        "x_post_psa": 0,
        "x_post_box": 1,
        "x_post_fixed": 2,
        "x_post_single": 3,
        "x_post_other": 4,
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

COMMON_CSS = ""
CSS_VERSION = "20260706-logo-header"


def html_shell(title, content, base_prefix="", extra_head=""):
    head_extra_html = f"{extra_head}\n" if extra_head else ""
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
{head_extra_html}<link rel="stylesheet" href="{base_prefix}assets/cardradar-theme.css?v={CSS_VERSION}">
</head>
<body>
{content}
</body>
</html>
"""


def logo_html(base_prefix=""):
    return f"""
<div class="logo-row">
  <div class="logo-mark logo-mark-image">
    <img src="{base_prefix}assets/cardradar-logo.png" alt="CardRadar" decoding="async">
  </div>
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

    <div class="hero-title">CardRadar</div>

    <p class="hero-copy">
      大阪・日本橋ページへ移動します。<br>
      移動しない場合は下のリンクをクリックしてください。
    </p>

    <div class="selector-grid">
      <a class="select-card" href="osaka-nihonbashi.html">
        <small>OSAKA</small>
        <strong>大阪・日本橋</strong>
        <p>大阪・日本橋周辺のポケカ買取表画像を見る。</p>
      </a>
    </div>

    <div class="updated">LAST UPDATE : {h(updated_at)}</div>
  </section>
</div>
<script>
window.location.replace("osaka-nihonbashi.html");
</script>
"""
    extra_head = '<meta http-equiv="refresh" content="0; url=osaka-nihonbashi.html">'
    return html_shell("CardRadar｜大阪・日本橋へ移動", content, extra_head=extra_head)


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
    shops = sort_shops_for_display(get_physical_shops("osaka-nihonbashi"))
    support_sources = get_support_sources()
    brands = get_unique_brands("osaka-nihonbashi")
    all_timeline_posts = get_timeline_posts(posts_by_source, "osaka-nihonbashi")
    timeline_posts, timeline_meta = select_timeline_posts_with_fallback(all_timeline_posts)

    media_items = {}
    timeline_html = ""
    timeline_initial_count = len(timeline_posts)
    latest_timeline_date = timeline_meta.get("latest_date", "")
    same_day_count = timeline_meta.get("latest_count", 0)
    if timeline_posts:
        timeline_notice = f"最新日：{format_date_label(latest_timeline_date)} / 最新日の投稿：{same_day_count}件"
        if timeline_meta.get("fallback_used"):
            timeline_notice += " / 前日以前も表示"
    else:
        timeline_notice = "最新日：未取得 / 最新日の投稿：0件"

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
      <img src="{h(image_url)}" alt="{h(post["shop_name"])}の買取表画像 {image_index + 1}" loading="lazy" decoding="async">
      <span class="zoom-badge">拡大</span>
      <span class="image-count">画像 {image_index + 1} / {image_count}</span>
      <span class="landscape-hint">横スクロールで確認</span>
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

    store_group_records = []
    store_panel_records = []
    store_initial_count = 0
    today_jst = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d")

    def store_view_status(meta, expanded_posts, shop_posts):
        latest_date = meta.get("latest_date", "")
        if not latest_date:
            dated_shop_posts = [post for post in shop_posts if post.get("posted_date_jst")]
            if dated_shop_posts:
                latest_date = max(post["posted_date_jst"] for post in dated_shop_posts)
        latest_obj = parse_jst_date(latest_date)
        reference_obj = parse_jst_date(latest_timeline_date) or latest_obj
        if not shop_posts or not latest_obj:
            return 4, "投稿なし / 取得待ち", "is-waiting"
        if latest_date == today_jst:
            return 0, "今日更新", "is-fresh"
        if latest_timeline_date and latest_date == latest_timeline_date:
            return 0, "最新日あり", "is-fresh"
        days_old = (reference_obj - latest_obj).days if reference_obj else 999
        if 0 <= days_old < STORE_VIEW_DEFAULT_DAYS:
            return 1, "過去7日あり", ""
        if 0 <= days_old < STORE_VIEW_EXPANDED_DAYS:
            return 2, "履歴あり", ""
        if expanded_posts:
            return 2, "履歴あり", ""
        return 3, "過去投稿あり", "is-past"

    for shop_index, shop in enumerate(shops):
        shop_posts = [normalize_post(post) for post in all_timeline_posts if post.get("shop_slug") == shop["shop_slug"]]
        default_shop_posts, expanded_shop_posts, store_view_meta = select_store_view_posts(shop_posts)

        display_types = []
        status_source_posts = expanded_shop_posts or shop_posts
        for post in status_source_posts:
            display_type = post.get("display_type", infer_display_type(post))
            if display_type not in display_types:
                display_types.append(display_type)
        type_text = " / ".join(short_type_label(t) for t in display_types) if display_types else "未分類"
        default_keys = store_view_meta["default_keys"]
        expanded_keys = store_view_meta["expanded_keys"]
        latest_store_date = store_view_meta.get("latest_date", "")
        status_order, status_label, status_class = store_view_status(store_view_meta, expanded_shop_posts, shop_posts)
        latest_date_label = format_date_label(latest_store_date) if latest_store_date else "未取得"
        default_post_count = len(default_shop_posts)
        expanded_post_count = len(expanded_shop_posts)
        extra_post_count = max(0, expanded_post_count - default_post_count)
        status_meta = (
            f"最新日：{latest_date_label} / 表示：{default_post_count}件 / 過去投稿：{expanded_post_count}件 / {type_text}"
            if shop_posts
            else f"最新日：未取得 / 表示：0件 / 過去投稿：0件 / {type_text}"
        )
        status_meta_html = (
            f'<span>最新日：{h(latest_date_label)}</span><span>表示：{default_post_count}件</span><span>過去投稿：{expanded_post_count}件</span><span class="store-group-types">{h(type_text)}</span>'
            if shop_posts
            else f'<span>最新日：未取得</span><span>表示：0件</span><span>過去投稿：0件</span><span class="store-group-types">{h(type_text)}</span>'
        )
        expanded_meta_parts = store_view_meta["expanded_meta"].split(" / ")
        expanded_meta_html = (
            "".join(f"<span>{h(part)}</span>" for part in expanded_meta_parts[:2])
            + (f'<span class="store-group-types">{h(" / ".join(expanded_meta_parts[2:]))}</span>' if len(expanded_meta_parts) > 2 else "")
            if expanded_shop_posts
            else status_meta_html
        )
        store_panel_waiting_class = " is-waiting" if not shop_posts else ""
        store_panel_latest = f"最新日：{h(latest_date_label)}" if shop_posts else "最新日：未取得"
        store_panel_count = f"過去投稿：{expanded_post_count}件" if shop_posts else "投稿なし / 取得待ち"
        store_panel_records.append((
            (1 if not shop_posts else 0, shop_index),
            f"""
<a class="store-panel-card{store_panel_waiting_class}"
   href="stores/{h(shop["shop_slug"])}.html"
   data-types="{h(' '.join(display_types))}"
   data-brand="{h(shop["brand_id"])}"
   data-search="{h(shop["shop_name"] + ' ' + shop["brand"] + ' ' + type_text)}">
  <div class="store-panel-name">{h(shop["shop_name"])}</div>
  <div class="store-panel-meta"><span class="store-status-badge {h(status_class)}">{h(status_label)}</span> {store_panel_latest} / {h(store_panel_count)}</div>
  <div class="store-panel-meta">{h(type_text)}</div>
  <div class="store-panel-link">店舗ページを見る →</div>
</a>
"""
        ))

        store_post_cards = ""
        has_default_posts = False
        expandable_post_keys = set()
        for post in expanded_shop_posts:
            image_urls = post.get("image_urls", [])
            if not image_urls:
                continue
            display_type = post.get("display_type", infer_display_type(post))
            type_label = short_type_label(display_type)
            media_id = f'timeline_{post.get("source_id", "post")}_{post.get("status_id", 0)}'
            image_count = len(image_urls)
            checked_label = format_update_label(post.get("posted_at") or post.get("collected_at", updated_at))
            identity = post_identity(post)
            in_default_range = "1" if identity in default_keys else "0"
            in_expanded_range = "1" if identity in expanded_keys else "0"
            if in_default_range != "1" and in_expanded_range == "1":
                expandable_post_keys.add(identity)
            age_badge = store_post_age_badge(post, latest_timeline_date or latest_store_date)
            age_badge_html = f' / <span class="store-age-badge">{h(age_badge)}</span>' if age_badge else ""
            is_table_split_candidate = post.get("brand_id") == "dragonstar"
            for image_index, image_url in enumerate(image_urls):
                table_controls = ""
                if is_table_split_candidate:
                    table_controls = """
          <div class="store-image-controls" aria-label="表ごと表示切替">
            <button type="button" class="store-table-mode-button is-active" data-table-mode="original" onclick="setStoreTableMode(event, this, 'original')">元画像</button>
            <button type="button" class="store-table-mode-button" data-table-mode="row3" onclick="setStoreTableMode(event, this, 'row3')">縦3分割</button>
            <button type="button" class="store-table-mode-button" data-table-mode="grid2x2" onclick="setStoreTableMode(event, this, 'grid2x2')">4分割</button>
            <button type="button" class="store-table-mode-button" data-table-mode="grid3x2" onclick="setStoreTableMode(event, this, 'grid3x2')">6分割</button>
          </div>"""
                image_position_label = f"画像 {image_index + 1} / {image_count}" if image_count > 1 else "画像"
                store_post_cards += f"""
      <article class="store-post-card"
        data-status="{h(post.get("status_id", 0))}"
        data-store="{h(post.get("shop_name", ""))}"
        data-types="{h(display_type)}"
        data-brand="{h(post.get("brand_id", ""))}"
        data-search="{h(post.get("shop_name", "") + ' ' + post.get("brand", "") + ' ' + post.get("buy_type_label", "") + ' ' + type_label + ' ' + post.get("summary", ""))}"
        data-range-default="{in_default_range}"
        data-range-expanded="{in_expanded_range}"
      >
        <div class="store-post-meta">確認：{h(checked_label)} / {h(type_label)} / {h(image_position_label)}{age_badge_html}</div>
        <div class="store-image-item" data-brand-id="{h(post.get("brand_id", ""))}" data-shop-slug="{h(post.get("shop_slug", ""))}" data-table-split-enabled="{str(is_table_split_candidate).lower()}">
          <div class="timeline-image store-post-image" role="button" tabindex="0" data-brand-id="{h(post.get("brand_id", ""))}" data-shop-slug="{h(post.get("shop_slug", ""))}" data-table-split-candidate="{str(is_table_split_candidate).lower()}" data-store-table-mode="original" onclick="openTimelineMedia('{h(media_id)}', {image_index})" onkeydown="handleStoreImageKey(event, '{h(media_id)}', {image_index})">
            <img src="{h(image_url)}" alt="{h(post["shop_name"])}の買取表画像 {image_index + 1}" loading="lazy" decoding="async">
          </div>{table_controls}
        </div>
        <div class="store-post-actions">
          <a href="{h(post["tweet_url"])}" target="_blank" rel="noopener noreferrer">Xで開く</a>
          <button type="button" onclick="openTimelineMedia('{h(media_id)}', {image_index})">拡大</button>
        </div>
      </article>
"""
            if in_default_range == "1":
                has_default_posts = True

        if not store_post_cards:
            if shop_posts:
                store_group_records.append((
                    (status_order, shop_index),
                    f"""
<section class="store-group is-past is-past-no-image"
  data-types="{h(' '.join(display_types))}"
  data-brand="{h(shop["brand_id"])}"
  data-search="{h(shop["shop_name"] + ' ' + shop["brand"] + ' ' + type_text)}"
  data-default-meta="{h(status_meta)}"
  data-expanded-meta="{h(status_meta)}"
  data-default-meta-html="{h(status_meta_html)}"
  data-expanded-meta-html="{h(status_meta_html)}"
  data-expanded="false"
  data-no-visible-posts="true"
>
  <div class="store-group-header">
    <div>
      <div class="store-group-title">
        <div class="store-group-name">{h(shop["shop_name"])}</div>
        <span class="store-status-badge {h(status_class)}">{h(status_label)}</span>
      </div>
      <div class="store-group-meta">{status_meta_html}</div>
      <div class="store-group-note">直近の表示対象はありません。<br>店舗ページで過去投稿を確認できます。</div>
      <a class="store-group-link store-group-past-link" href="stores/{h(shop["shop_slug"])}.html">店舗ページを見る →</a>
    </div>
  </div>
</section>
"""
                ))
                continue
            store_group_records.append((
                (4, shop_index),
                f"""
<section class="store-group is-waiting"
  data-types=""
  data-brand="{h(shop["brand_id"])}"
  data-search="{h(shop["shop_name"] + ' ' + shop["brand"])}"
  data-default-meta="{h(status_meta)}"
  data-expanded-meta="{h(status_meta)}"
  data-expanded="false"
  data-waiting="true"
>
  <div class="store-group-header">
    <div>
      <div class="store-group-title">
        <div class="store-group-name">{h(shop["shop_name"])}</div>
        <span class="store-status-badge is-waiting">取得待ち</span>
      </div>
      <div class="store-group-meta">最新の買取表はまだ取得できていません / 表示：0件</div>
    </div>
  </div>
</section>
"""
            ))
            continue
        if has_default_posts:
            store_initial_count += 1
        extra_post_count = len(expandable_post_keys)
        expand_button_html = (
            f'<button class="store-expand-button" type="button" data-more-label="さらに表示（+{extra_post_count}件）" data-less-label="最新だけ表示" onclick="toggleStoreGroupExpanded(this)">さらに表示（+{extra_post_count}件）</button>'
            if extra_post_count > 0 else ""
        )

        store_group_records.append((
            (status_order, shop_index),
            f"""
<section class="store-group"
  data-types="{h(' '.join(display_types))}"
  data-brand="{h(shop["brand_id"])}"
  data-search="{h(shop["shop_name"] + ' ' + shop["brand"] + ' ' + type_text)}"
  data-default-meta="{h(status_meta)}"
  data-expanded-meta="{h(store_view_meta["expanded_meta"])}"
  data-default-meta-html="{h(status_meta_html)}"
  data-expanded-meta-html="{h(expanded_meta_html)}"
  data-expanded="false"
>
  <div class="store-group-header">
    <div>
      <div class="store-group-title">
        <div class="store-group-name">{h(shop["shop_name"])}</div>
        <span class="store-status-badge {h(status_class)}">{h(status_label)}</span>
      </div>
      <div class="store-group-meta">{status_meta_html}</div>
    </div>
    <div class="store-group-actions">
      {expand_button_html}
    </div>
  </div>
  <div class="store-post-carousel">
{store_post_cards}
  </div>
</section>
"""
        ))

    store_groups_html = "".join(html for _, html in sorted(store_group_records, key=lambda item: item[0]))
    store_panel_html = "".join(html for _, html in sorted(store_panel_records, key=lambda item: item[0]))

    initial_result_count = store_initial_count
    no_result_class = "no-result hidden" if initial_result_count else "no-result"
    no_result_attrs = ' hidden aria-hidden="true" style="display:none"' if initial_result_count else ' aria-hidden="false"'
    nav_store_links = "\n".join(
        f'<a href="stores/{h(shop["shop_slug"])}.html" onclick="closeMenu()">{h(shop["shop_name"])}</a>'
        for shop in shops
    )

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
<button class="filter-chip" data-brand-id="{h(brand["id"])}" data-brand-label="{h(brand["label"])}" onclick="toggleBrand('{h(brand["id"])}', this)">{h(brand["label"])}</button>
"""

    media_json = json_for_script(media_items)
    store_view_css = ""

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

  {store_view_css}

  <div class="search-area" id="searchArea">
    <div class="search-line">
      <input id="searchInput" class="search-input" type="search" placeholder="店舗・カード名で検索">
      <div class="result-line">表示：<span class="result-count">{initial_result_count}</span>件</div>
    </div>

    <div class="view-switch" role="group" aria-label="表示切替">
      <button id="storeViewButton" class="view-toggle active" type="button" onclick="setViewMode('store')">店舗別</button>
      <button id="timelineViewButton" class="view-toggle" type="button" onclick="setViewMode('timeline')">新着順</button>
      <button id="storeListViewButton" class="view-toggle" type="button" onclick="setViewMode('list')">店舗リスト</button>
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

    <div class="brand-panel" id="brandPanel" aria-hidden="true">
      <div class="brand-tools">
        <input id="brandSearchInput" class="brand-search" type="search" placeholder="店舗名で検索" aria-label="店舗名で検索" oninput="filterBrandOptions()">
        <button class="brand-clear-button" type="button" onclick="clearBrandFilters()">全解除</button>
      </div>
      <div class="selected-brand-row" id="selectedBrandRow" aria-live="polite"></div>
      <div class="brand-row">
        {brand_buttons}
      </div>
      <button class="reset-button" onclick="resetFilters()">リセット</button>
    </div>
  </div>

  <div class="compact-search-bar" id="compactSearchBar">
    <div class="compact-line">
      <button class="tool-button menu-button" type="button" aria-label="メニュー" onclick="openMenu()">☰</button>
      <input id="compactSearchInput" class="search-input" type="search" placeholder="検索">
      <div class="result-line"><span class="result-count">{initial_result_count}</span>件</div>
    </div>
    <div class="type-row compact-type-row">
      {type_buttons}
    </div>
  </div>

  <main>
    <div id="timelineView" class="view-panel hidden">
      <div class="section-head">
        <h2>新着TL</h2>
        <p>1ツイート1カードで表示 / {h(timeline_notice)}</p>
      </div>

      <div class="timeline-list" id="timelineList">
        {timeline_html}
      </div>
    </div>

    <div id="storeView" class="view-panel store-view-section">
      <!-- 店舗別ビューの表示範囲 controls are generated from test.py for the published Osaka/Nipponbashi HTML. -->
      <div class="section-head">
        <h2>店舗別ビュー</h2>
        <p>店舗別ビューでは過去7日を表示。投稿が少ない店舗は最新投稿も補完します。</p>
      </div>

      <div class="store-group-list" id="storeGroupList">
        {store_groups_html}
      </div>
    </div>

    <div id="storeListView" class="view-panel hidden">
      <div class="section-head">
        <h2>店舗リスト</h2>
        <p>店舗詳細ページで過去投稿をまとめて確認できます。</p>
      </div>
      <div class="store-panel" id="storePanel">
        {store_panel_html}
      </div>
    </div>

    <div class="{no_result_class}" id="noResult"{no_result_attrs}>該当する買取投稿はありません。<br>条件を変更してください。</div>

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
      <a href="osaka-nihonbashi.html#support-links" onclick="closeMenu()">公式Web買取表</a>
      <a href="osaka-nihonbashi.html#support-links" onclick="closeMenu()">相場確認</a>
      <a href="#">掲載について</a>
    </div>
    <div class="nav-store-list">
      <button class="nav-store-toggle" type="button" aria-expanded="false" aria-controls="navStoreLinks" onclick="toggleNavStoreList()">店舗一覧</button>
      <div class="nav-store-links" id="navStoreLinks" hidden>
        {nav_store_links}
      </div>
    </div>
  </nav>
</div>

<div class="modal" id="timelineMediaModal">
  <div class="modal-inner">
    <button class="modal-close" onclick="closeTimelineMedia()">閉じる</button>
    <div class="modal-image-wrap" id="timelineModalImageWrap">
      <img class="modal-image" id="timelineModalImage" src="" alt="買取表画像">
      <span class="landscape-hint">横スクロールで確認</span>
    </div>
    <div class="modal-nav">
      <button type="button" onclick="showTimelineImage(-1)">前へ</button>
      <span class="modal-counter" id="timelineModalCounter">画像 1 / 1</span>
      <button type="button" onclick="showTimelineImage(1)">次へ</button>
    </div>
    <div class="modal-summary" id="timelineModalSummary"></div>
    <div class="modal-actions">
      <a id="timelineModalImageLink" href="#" target="_blank" rel="noopener noreferrer">画像だけ開く</a>
      <a id="timelineModalTweetLink" href="#" target="_blank" rel="noopener noreferrer">Xで開く</a>
    </div>
  </div>
</div>

<script>
const selectedTypes = new Set();
const selectedBrands = new Set();
const TIMELINE_MEDIA = {media_json};
let currentSort = "new";
let currentView = "store";
let currentStoreRange = "week";
let currentMediaItem = null;
let currentMediaIndex = 0;

function openMenu() {{
  document.getElementById("navOverlay").classList.add("open");
}}

function closeMenu(event) {{
  if (event && event.target !== document.getElementById("navOverlay")) return;
  document.getElementById("navOverlay").classList.remove("open");
  const toggle = document.querySelector(".nav-store-toggle");
  const links = document.getElementById("navStoreLinks");
  if (toggle && links) {{
    toggle.setAttribute("aria-expanded", "false");
    links.hidden = true;
  }}
}}

function toggleNavStoreList() {{
  const toggle = document.querySelector(".nav-store-toggle");
  const links = document.getElementById("navStoreLinks");
  if (!toggle || !links) return;
  const isOpen = toggle.getAttribute("aria-expanded") === "true";
  toggle.setAttribute("aria-expanded", isOpen ? "false" : "true");
  links.hidden = isOpen;
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
  const image = getHighResImageUrl(images[currentMediaIndex]);
  const modalImage = document.getElementById("timelineModalImage");
  const modalWrap = document.getElementById("timelineModalImageWrap");

  if (modalWrap) modalWrap.classList.remove("is-landscape");
  modalImage.src = image || "";
  modalImage.onload = () => markLandscapeImage(modalImage);
  document.getElementById("timelineModalCounter").textContent = `画像 ${{currentMediaIndex + 1}} / ${{Math.max(images.length, 1)}}`;
  document.getElementById("timelineModalSummary").textContent = `${{currentMediaItem.shop_name}} / ${{currentMediaItem.type_label}} / 確認：${{currentMediaItem.checked_at}}${{currentMediaItem.summary ? " / " + currentMediaItem.summary : ""}}`;
  document.getElementById("timelineModalImageLink").href = image || "#";
  document.getElementById("timelineModalTweetLink").href = currentMediaItem.tweet_url;
  if (modalImage.complete) markLandscapeImage(modalImage);
}}

function openTimelineMedia(id, startIndex = 0) {{
  currentMediaItem = TIMELINE_MEDIA[id];
  if (!currentMediaItem) return;
  const count = (currentMediaItem.image_urls || []).length;
  currentMediaIndex = count ? Math.min(Math.max(Number(startIndex) || 0, 0), count - 1) : 0;
  renderTimelineMedia();
  document.getElementById("timelineMediaModal").classList.add("open");
}}

function handleStoreImageKey(event, id, startIndex = 0) {{
  if (event.key !== "Enter" && event.key !== " ") return;
  event.preventDefault();
  openTimelineMedia(id, startIndex);
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

function getHighResImageUrl(url) {{
  if (!url || !url.includes("pbs.twimg.com/media/")) return url;
  try {{
    const parsed = new URL(url, window.location.href);
    parsed.searchParams.set("name", "orig");
    return parsed.toString();
  }} catch (e) {{
    return url
      .replace("name=small", "name=orig")
      .replace("name=medium", "name=orig")
      .replace("name=large", "name=orig");
  }}
}}

function upgradeImageElement(img) {{
  if (!img) return "";
  const highResUrl = getHighResImageUrl(img.getAttribute("src") || img.src);
  if (highResUrl) img.dataset.highresUrl = highResUrl;
  if (highResUrl && highResUrl !== img.src) img.src = highResUrl;
  return highResUrl;
}}

function getStableLandscapeMetrics(img) {{
  if (!img) return {{ ratio: 1.6, sourceUrl: "" }};
  const sourceUrl = img.dataset.highresUrl || getHighResImageUrl(img.getAttribute("src") || img.currentSrc || img.src);
  if (sourceUrl) img.dataset.highresUrl = sourceUrl;
  const naturalWidth = Number(img.dataset.naturalWidth) || img.naturalWidth || 0;
  const naturalHeight = Number(img.dataset.naturalHeight) || img.naturalHeight || 0;
  if (!img.dataset.naturalWidth && img.naturalWidth && img.naturalHeight) {{
    img.dataset.naturalWidth = String(img.naturalWidth);
    img.dataset.naturalHeight = String(img.naturalHeight);
  }}
  const cachedRatio = Number(img.dataset.landscapeRatio);
  const ratio = cachedRatio || (naturalWidth && naturalHeight ? naturalWidth / naturalHeight : 1.6);
  if (!img.dataset.landscapeRatio && naturalWidth && naturalHeight) {{
    img.dataset.landscapeRatio = String(ratio);
  }}
  return {{ ratio, sourceUrl: sourceUrl || img.currentSrc || img.src }};
}}

function markLandscapeImage(img) {{
  if (!img || !img.naturalWidth || !img.naturalHeight) return;
  const {{ ratio }} = getStableLandscapeMetrics(img);
  const target = img.closest(".timeline-image, .image-card, .modal-image-wrap");
  if (!target) return;
  const isLandscape = ratio >= 1.35 || isDragonstarStoreViewImage(target);
  target.classList.toggle("is-landscape", isLandscape);
  if (isLandscape) renderLandscapeView(target, img);
  else {{
    target.querySelector(".landscape-split")?.remove();
    target.querySelector(".landscape-mode-switch")?.remove();
    target.classList.remove("landscape-mode-original", "landscape-mode-half", "landscape-mode-quarter", "landscape-mode-table");
  }}
  setupScrollIndicators(target);
}}

function getLandscapeMode() {{
  const saved = localStorage.getItem("cardradarLandscapeMode");
  return ["original", "half", "quarter", "table"].includes(saved) ? saved : "half";
}}

function setLandscapeMode(mode) {{
  const nextMode = ["original", "half", "quarter", "table"].includes(mode) ? mode : "half";
  localStorage.setItem("cardradarLandscapeMode", nextMode);
  document.querySelectorAll(".is-landscape").forEach(target => {{
    const img = target.querySelector(":scope > img, :scope > .modal-image");
    if (img) renderLandscapeView(target, img);
  }});
  setupScrollIndicators();
}}

function isDragonstarStoreViewImage(target) {{
  if (!target?.classList?.contains("store-post-image")) return false;
  if (target.dataset.tableSplitCandidate === "true") return true;
  if (target.dataset.brandId === "dragonstar") return true;
  const item = target.closest(".store-image-item");
  if (item?.dataset?.tableSplitEnabled === "true") return true;
  if (item?.dataset?.brandId === "dragonstar") return true;
  const card = target.closest(".store-post-card");
  return card?.dataset?.brand === "dragonstar";
}}

function syncStoreTableControls(target, mode) {{
  const item = target?.closest(".store-image-item");
  if (!item) return;
  item.querySelectorAll(".store-table-mode-button").forEach(button => {{
    button.classList.toggle("is-active", button.dataset.tableMode === mode);
  }});
}}

function setStoreTableMode(event, button, mode) {{
  event.preventDefault();
  event.stopPropagation();
  const item = button.closest(".store-image-item");
  const target = item?.querySelector(".store-post-image");
  const img = target?.querySelector(":scope > img");
  if (!target || !img) return;
  const nextMode = ["row3", "grid3x2", "grid2x2"].includes(mode) ? mode : "original";
  target.dataset.storeTableMode = nextMode;
  target.classList.add("is-landscape");
  renderLandscapeView(target, img);
  setupScrollIndicators(target);
}}

function renderLandscapeModeSwitch(target, mode) {{
  let controls = target.querySelector(".landscape-mode-switch");
  if (isDragonstarStoreViewImage(target)) {{
    controls?.remove();
    return;
  }}
  if (!controls) {{
    controls = document.createElement("span");
    controls.className = "landscape-mode-switch";
    target.appendChild(controls);
  }}
  const isStoreViewImage = target.classList.contains("store-post-image");
  const isDragonstarTableImage = isDragonstarStoreViewImage(target);
  const modes = isDragonstarTableImage ? ["original", "table"] : ["original", "half", "quarter"];
  controls.innerHTML = modes.map(item => {{
    const labels = isDragonstarTableImage
      ? {{ original: "元画像", table: "表ごと" }}
      : isStoreViewImage
        ? {{ original: "元画像", half: "2分割", quarter: "4分割" }}
        : {{ original: "元画像", half: "縦1/2", quarter: "縦横1/4" }};
    return `<span class="landscape-mode-button ${{item === mode ? "is-active" : ""}}" role="button" tabindex="0" data-landscape-mode="${{item}}">${{labels[item]}}</span>`;
  }}).join("");
  controls.querySelectorAll(".landscape-mode-button").forEach(button => {{
    const activate = event => {{
      event.preventDefault();
      event.stopPropagation();
      if (isStoreViewImage && !isDragonstarTableImage) {{
        target.dataset.storeLandscapeMode = button.dataset.landscapeMode;
        const img = target.querySelector(":scope > img");
        if (img) renderLandscapeView(target, img);
        setupScrollIndicators(target);
        return;
      }}
      setLandscapeMode(button.dataset.landscapeMode);
    }};
    button.addEventListener("click", activate);
    button.addEventListener("keydown", event => {{
      if (event.key === "Enter" || event.key === " ") activate(event);
    }});
  }});
}}

function getDragonstarTableGrid(mode) {{
  if (mode === "grid2x2") return {{ cols: 2, rows: 2, className: "table-split-mode-grid2x2" }};
  if (mode === "grid3x2") return {{ cols: 3, rows: 2, className: "table-split-mode-grid3x2" }};
  return {{ cols: 3, rows: 1, className: "table-split-mode-row3" }};
}}

function getStoreTableSliceKey(card) {{
  if (!card) return "";
  if (!card.dataset.storeTableSliceKey) {{
    card.dataset.storeTableSliceKey = `storeTable_${{Math.random().toString(36).slice(2)}}`;
  }}
  return card.dataset.storeTableSliceKey;
}}

function clearStoreTableRailSlices(target) {{
  const card = target?.closest(".store-post-card");
  const carousel = card?.closest(".store-post-carousel");
  if (!card || !carousel) return;
  const key = card.dataset.storeTableSliceKey;
  if (!key) return;
  carousel.querySelectorAll(`[data-store-table-slice-for="${{key}}"]`).forEach(item => item.remove());
}}

function makeStoreTableSliceHtml(sourceUrl, grid, ratio, index, x, y) {{
  const total = grid.cols * grid.rows;
  return `
    <div class="landscape-slice store-table-slice" style="--table-cols:${{grid.cols}}; --table-rows:${{grid.rows}}; --table-slice-ratio:${{((ratio * grid.rows) / grid.cols).toFixed(4)}}; --table-bg-x:${{x}}%; --table-bg-y:${{y}}%; --table-image:url('${{sourceUrl}}')">
      <span class="landscape-slice-label">表${{index}} / ${{total}}</span>
      <span class="landscape-slice-frame table-split-frame"><span class="table-split-slice" aria-hidden="true"></span></span>
    </div>`;
}}

function makeStoreLandscapeSliceHtml(sourceUrl, label, sliceClass) {{
  return `
    <div class="landscape-slice ${{sliceClass}}">
      <span class="landscape-slice-label">${{label}}</span>
      <span class="landscape-slice-frame"><img src="${{sourceUrl}}" alt=""></span>
    </div>`;
}}

function renderStoreLandscapeRailSlices(target, mode, sourceUrl, slices) {{
  const card = target?.closest(".store-post-card");
  const carousel = card?.closest(".store-post-carousel");
  if (!card || !carousel) return;
  clearStoreTableRailSlices(target);
  const key = getStoreTableSliceKey(card);
  const actionHtml = card.querySelector(".store-post-actions")?.outerHTML || "";
  const baseMeta = card.querySelector(".store-post-meta")?.textContent?.trim() || "";
  const modeClass = mode === "quarter" ? "landscape-mode-quarter" : "landscape-mode-half";
  let insertAfter = card;
  slices.slice(1).forEach(slice => {{
    const clone = document.createElement("article");
    clone.className = "store-post-card store-table-slice-card";
    Object.entries(card.dataset).forEach(([name, value]) => {{
      clone.dataset[name] = value;
    }});
    clone.dataset.storeTableSliceFor = key;
    clone.innerHTML = `
      <div class="store-post-meta">${{baseMeta}} / ${{slice.label}}</div>
      <div class="store-image-item" data-brand-id="${{target.dataset.brandId || ""}}" data-shop-slug="${{target.dataset.shopSlug || ""}}">
        <div class="timeline-image store-post-image store-table-slice-image is-landscape ${{modeClass}}" role="button" tabindex="0" onclick="${{target.getAttribute("onclick") || ""}}" onkeydown="${{target.getAttribute("onkeydown") || ""}}">
          <div class="landscape-split store-view-landscape-split">
            ${{makeStoreLandscapeSliceHtml(sourceUrl, slice.label, slice.className)}}
          </div>
        </div>
      </div>
      ${{actionHtml}}
    `;
    insertAfter.insertAdjacentElement("afterend", clone);
    insertAfter = clone;
  }});
}}

function renderStoreTableRailSlices(target, grid, ratio, sourceUrl, slices) {{
  const card = target?.closest(".store-post-card");
  const carousel = card?.closest(".store-post-carousel");
  if (!card || !carousel) return;
  clearStoreTableRailSlices(target);
  const key = getStoreTableSliceKey(card);
  const actionHtml = card.querySelector(".store-post-actions")?.outerHTML || "";
  const baseMeta = card.querySelector(".store-post-meta")?.textContent?.trim() || "";
  let insertAfter = card;
  slices.slice(1).forEach(slice => {{
    const clone = document.createElement("article");
    clone.className = "store-post-card store-table-slice-card";
    Object.entries(card.dataset).forEach(([name, value]) => {{
      clone.dataset[name] = value;
    }});
    clone.dataset.storeTableSliceFor = key;
    clone.innerHTML = `
      <div class="store-post-meta">${{baseMeta}} / 表${{slice.index}} / ${{slices.length}}</div>
      <div class="store-image-item" data-brand-id="${{target.dataset.brandId || ""}}" data-shop-slug="${{target.dataset.shopSlug || ""}}">
        <div class="timeline-image store-post-image store-table-slice-image is-landscape landscape-mode-table" role="button" tabindex="0" onclick="${{target.getAttribute("onclick") || ""}}" onkeydown="${{target.getAttribute("onkeydown") || ""}}">
          <div class="landscape-split store-view-landscape-split ${{grid.className}}">
            ${{makeStoreTableSliceHtml(sourceUrl, grid, ratio, slice.index, slice.x, slice.y)}}
          </div>
        </div>
      </div>
      ${{actionHtml}}
    `;
    clone.querySelectorAll(".landscape-slice-label").forEach(label => label.remove());
    insertAfter.insertAdjacentElement("afterend", clone);
    insertAfter = clone;
  }});
}}

function renderLandscapeView(target, img) {{
  const savedMode = getLandscapeMode();
  const {{ ratio, sourceUrl }} = getStableLandscapeMetrics(img);
  const isStoreViewImage = target.classList.contains("store-post-image");
  const isDragonstarTableImage = isDragonstarStoreViewImage(target);
  const storeTableMode = isDragonstarTableImage ? (target.dataset.storeTableMode || "original") : "";
  const mode = isDragonstarTableImage
    ? (storeTableMode === "original" ? "original" : "table")
    : (isStoreViewImage ? (target.dataset.storeLandscapeMode || "original")
    : (savedMode === "table" ? "half" : savedMode));
  target.classList.toggle("landscape-mode-original", mode === "original");
  target.classList.toggle("landscape-mode-half", mode === "half");
  target.classList.toggle("landscape-mode-quarter", mode === "quarter");
  target.classList.toggle("landscape-mode-table", mode === "table");
  renderLandscapeModeSwitch(target, mode);
  if (isDragonstarTableImage) syncStoreTableControls(target, storeTableMode);
  let split = target.querySelector(".landscape-split");
  if (!split) {{
    split = document.createElement("div");
    split.className = "landscape-split";
    img.insertAdjacentElement("afterend", split);
  }}
  split.classList.toggle("store-view-landscape-split", target.classList.contains("store-post-image"));
  split.classList.remove("table-split-mode-row3", "table-split-mode-grid3x2", "table-split-mode-grid2x2");
  if (mode === "original") {{
    clearStoreTableRailSlices(target);
    split.innerHTML = "";
    return;
  }}
  if (mode === "table") {{
    const grid = getDragonstarTableGrid(storeTableMode);
    split.classList.add(grid.className);
    split.style.setProperty("--table-cols", grid.cols);
    split.style.setProperty("--table-rows", grid.rows);
    split.style.setProperty("--table-slice-ratio", ((ratio * grid.rows) / grid.cols).toFixed(4));
    split.style.removeProperty("--landscape-panel-ratio");
    const slices = [];
    for (let row = 0; row < grid.rows; row += 1) {{
      for (let col = 0; col < grid.cols; col += 1) {{
        const index = row * grid.cols + col + 1;
        const x = grid.cols === 1 ? 0 : (col / (grid.cols - 1)) * 100;
        const y = grid.rows === 1 ? 0 : (row / (grid.rows - 1)) * 100;
        slices.push({{ index, x, y }});
      }}
    }}
    split.innerHTML = makeStoreTableSliceHtml(sourceUrl, grid, ratio, slices[0].index, slices[0].x, slices[0].y);
    if (isDragonstarTableImage) renderStoreTableRailSlices(target, grid, ratio, sourceUrl, slices);
    return;
  }}
  clearStoreTableRailSlices(target);
  if (mode === "quarter") {{
    split.style.setProperty("--landscape-panel-ratio", ratio.toFixed(4));
    const labels = isStoreViewImage
      ? ["4分割：左上", "4分割：右上", "4分割：左下", "4分割：右下"]
      : ["左上", "右上", "左下", "右下"];
    const quarterSlices = [
      {{ label: labels[0], className: "is-top-left" }},
      {{ label: labels[1], className: "is-top-right" }},
      {{ label: labels[2], className: "is-bottom-left" }},
      {{ label: labels[3], className: "is-bottom-right" }},
    ];
    split.innerHTML = isStoreViewImage
      ? makeStoreLandscapeSliceHtml(sourceUrl, quarterSlices[0].label, quarterSlices[0].className)
      : quarterSlices.map(slice => makeStoreLandscapeSliceHtml(sourceUrl, slice.label, slice.className)).join("");
    if (isStoreViewImage) renderStoreLandscapeRailSlices(target, "quarter", sourceUrl, quarterSlices);
    return;
  }}
  split.style.removeProperty("--landscape-panel-ratio");
  const halfLabels = isStoreViewImage ? ["2分割：左", "2分割：右"] : ["左半分", "右半分"];
  const halfSlices = [
    {{ label: halfLabels[0], className: "is-left" }},
    {{ label: halfLabels[1], className: "is-right" }},
  ];
  split.innerHTML = isStoreViewImage
    ? makeStoreLandscapeSliceHtml(sourceUrl, halfSlices[0].label, halfSlices[0].className)
    : halfSlices.map(slice => makeStoreLandscapeSliceHtml(sourceUrl, slice.label, slice.className)).join("");
  if (isStoreViewImage) renderStoreLandscapeRailSlices(target, "half", sourceUrl, halfSlices);
}}

function bindLandscapeImages(root = document) {{
  root.querySelectorAll(".timeline-image img, .image-card img").forEach(img => {{
    upgradeImageElement(img);
    img.addEventListener("load", () => markLandscapeImage(img));
    if (img.complete) markLandscapeImage(img);
  }});
}}

function getScrollIndicatorHost(el) {{
  if (el.matches(".store-post-strip, .store-post-image-list")) return el.parentElement || el;
  return el;
}}

function ensureScrollIndicator(el) {{
  const host = getScrollIndicatorHost(el);
  let indicator = el.dataset.scrollIndicatorId
    ? document.getElementById(el.dataset.scrollIndicatorId)
    : null;
  if (!indicator) {{
    indicator = document.createElement("span");
    indicator.className = "scroll-progress";
    indicator.id = `scrollIndicator_${{Math.random().toString(36).slice(2)}}`;
    el.dataset.scrollIndicatorId = indicator.id;
    if (el.matches(".store-post-strip, .store-post-image-list")) {{
      el.insertAdjacentElement("afterend", indicator);
    }} else {{
      host.appendChild(indicator);
    }}
  }}
  return indicator;
}}

function updateScrollIndicator(el) {{
  if (!el || !el.isConnected) return;
  const maxScroll = Math.max(0, el.scrollWidth - el.clientWidth);
  const canScroll = maxScroll > 4;
  el.classList.toggle("scroll-aware", canScroll);
  el.classList.toggle("can-scroll-left", canScroll && el.scrollLeft > 4);
  el.classList.toggle("can-scroll-right", canScroll && el.scrollLeft < maxScroll - 4);
  const indicator = ensureScrollIndicator(el);
  indicator.classList.toggle("is-visible", canScroll);
  if (!canScroll) return;
  const total = Math.max(2, Math.ceil(el.scrollWidth / Math.max(el.clientWidth, 1)));
  const current = Math.min(total, Math.max(1, Math.round((el.scrollLeft / Math.max(maxScroll, 1)) * (total - 1)) + 1));
  indicator.textContent = `${{current}} / ${{total}}`;
}}

function setupScrollIndicators(root = document) {{
  const scope = root instanceof Element ? root : document;
  const targets = new Set();
  if (scope.matches?.(".store-post-strip, .store-post-image-list, .timeline-image.is-landscape, .image-card.is-landscape, .modal-image-wrap.is-landscape, .landscape-split")) targets.add(scope);
  scope.querySelectorAll?.(".store-post-strip, .store-post-image-list, .timeline-image.is-landscape, .image-card.is-landscape, .modal-image-wrap.is-landscape, .landscape-split").forEach(el => targets.add(el));
  targets.forEach(el => {{
    if (!el.dataset.scrollAwareBound) {{
      el.dataset.scrollAwareBound = "1";
      let ticking = false;
      el.addEventListener("scroll", () => {{
        if (ticking) return;
        ticking = true;
        requestAnimationFrame(() => {{
          ticking = false;
          updateScrollIndicator(el);
        }});
      }}, {{ passive: true }});
    }}
    requestAnimationFrame(() => updateScrollIndicator(el));
  }});
}}

function syncTypeButtons() {{
  document.querySelectorAll(".type-row .filter-chip").forEach(btn => {{
    const type = btn.dataset.type;
    btn.classList.toggle("active", selectedTypes.size === 0 ? type === "all" : selectedTypes.has(type));
  }});
}}

function getBrandButton(brand) {{
  return Array.from(document.querySelectorAll(".brand-row .filter-chip")).find(btn => btn.dataset.brandId === brand);
}}

function syncBrandButtons() {{
  document.querySelectorAll(".brand-row .filter-chip").forEach(btn => {{
    btn.classList.toggle("active", selectedBrands.has(btn.dataset.brandId));
  }});
}}

function renderSelectedBrands() {{
  const row = document.getElementById("selectedBrandRow");
  if (!row) return;
  row.innerHTML = "";
  selectedBrands.forEach(brand => {{
    const button = getBrandButton(brand);
    const label = button?.dataset?.brandLabel || brand;
    const chip = document.createElement("span");
    chip.className = "selected-brand-chip";
    const labelText = document.createElement("span");
    labelText.textContent = label;
    const removeButton = document.createElement("button");
    removeButton.type = "button";
    removeButton.textContent = "×";
    removeButton.setAttribute("aria-label", `${{label}}を解除`);
    removeButton.addEventListener("click", () => removeBrandFilter(brand));
    chip.append(labelText, removeButton);
    row.appendChild(chip);
  }});
}}

function filterBrandOptions() {{
  const input = document.getElementById("brandSearchInput");
  const query = (input?.value || "").trim().toLowerCase();
  document.querySelectorAll(".brand-row .filter-chip").forEach(btn => {{
    const label = (btn.dataset.brandLabel || btn.textContent || "").toLowerCase();
    const id = (btn.dataset.brandId || "").toLowerCase();
    btn.classList.toggle("hidden", !!query && !label.includes(query) && !id.includes(query));
  }});
}}

function removeBrandFilter(brand) {{
  selectedBrands.delete(brand);
  syncBrandButtons();
  renderSelectedBrands();
  applyFilters();
}}

function clearBrandFilters() {{
  selectedBrands.clear();
  syncBrandButtons();
  renderSelectedBrands();
  applyFilters();
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
  if (selectedBrands.has(brand)) {{ selectedBrands.delete(brand); }}
  else {{ selectedBrands.add(brand); }}
  syncBrandButtons();
  renderSelectedBrands();
  applyFilters();
}}

function resetFilters() {{
  selectedTypes.clear();
  selectedBrands.clear();
  document.querySelectorAll(".search-input").forEach(input => input.value = "");
  const brandSearch = document.getElementById("brandSearchInput");
  if (brandSearch) brandSearch.value = "";
  document.querySelectorAll(".filter-chip").forEach(btn => btn.classList.remove("active"));
  syncTypeButtons();
  syncBrandButtons();
  renderSelectedBrands();
  filterBrandOptions();
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

function getVisibleStoreListCards() {{
  const list = document.getElementById("storePanel");
  if (!list) return [];
  return Array.from(list.querySelectorAll(":scope > .store-panel-card")).filter(card => {{
    if (card.classList.contains("hidden")) return false;
    if (card.closest(".view-panel.hidden")) return false;
    return !!(card.offsetWidth || card.offsetHeight || card.getClientRects().length);
  }});
}}

function getVisibleActiveCards() {{
  if (currentView === "store") return getVisibleStoreGroups();
  if (currentView === "list") return getVisibleStoreListCards();
  return getVisibleTimelineCards();
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

function updateStoreRangeButtons() {{
  const latestButton = document.getElementById("storeRangeLatestButton");
  const weekButton = document.getElementById("storeRangeWeekButton");
  if (latestButton) {{
    latestButton.classList.toggle("active", currentStoreRange === "latest");
    latestButton.setAttribute("aria-pressed", currentStoreRange === "latest" ? "true" : "false");
  }}
  if (weekButton) {{
    weekButton.classList.toggle("active", currentStoreRange === "week");
    weekButton.setAttribute("aria-pressed", currentStoreRange === "week" ? "true" : "false");
  }}
}}

function isStoreCardInCurrentRange(card) {{
  if (!card) return false;
  const group = card.closest(".store-group");
  if (group && group.dataset.expanded === "true") return card.dataset.rangeExpanded === "1";
  return card.dataset.rangeDefault === "1";
}}

function updateStoreRangeVisibility() {{
  document.querySelectorAll(".store-post-card").forEach(card => {{
    const shouldShow = isStoreCardInCurrentRange(card);
    card.classList.toggle("range-hidden", !shouldShow);
    card.dataset.rangeVisible = shouldShow ? "1" : "0";
  }});
  document.querySelectorAll(".store-group").forEach(group => {{
    const expanded = group.dataset.expanded === "true";
    const meta = expanded ? group.dataset.expandedMeta : group.dataset.defaultMeta;
    const metaHtml = expanded ? group.dataset.expandedMetaHtml : group.dataset.defaultMetaHtml;
    const metaEl = group.querySelector(".store-group-meta");
    if (metaEl && (metaHtml || meta)) metaEl.innerHTML = metaHtml || meta;
    const button = group.querySelector(".store-expand-button");
    if (button) {{
      button.textContent = expanded ? (button.dataset.lessLabel || "最新だけ表示") : (button.dataset.moreLabel || "さらに表示");
      button.setAttribute("aria-expanded", expanded ? "true" : "false");
    }}
  }});
}}

function setStoreRangeMode(mode) {{
  currentStoreRange = "week";
  updateStoreRangeButtons();
  updateStoreRangeVisibility();
  applyFilters();
  requestAnimationFrame(() => setupScrollIndicators());
}}

function toggleStoreGroupExpanded(button) {{
  const group = button.closest(".store-group");
  if (!group) return;
  group.dataset.expanded = group.dataset.expanded === "true" ? "false" : "true";
  updateStoreRangeVisibility();
  applyFilters();
  requestAnimationFrame(() => setupScrollIndicators());
}}

function applyFilters() {{
  const search = document.getElementById("searchInput").value.trim().toLowerCase();
  document.querySelectorAll(".timeline-post").forEach(post => post.classList.toggle("hidden", !matchesItem(post, search)));
  document.querySelectorAll(".store-group").forEach(group => {{
    if (group.dataset.waiting === "true" || group.dataset.noVisiblePosts === "true") {{
      group.classList.toggle("hidden", !matchesItem(group, search));
      return;
    }}
    let visibleChildren = 0;
    group.querySelectorAll(".store-post-card").forEach(card => {{
      const rangeOk = isStoreCardInCurrentRange(card);
      const cardMatches = rangeOk && matchesItem(card, search);
      card.classList.toggle("range-hidden", !rangeOk);
      card.dataset.rangeVisible = rangeOk ? "1" : "0";
      card.classList.toggle("hidden", !cardMatches);
      if (cardMatches) visibleChildren += 1;
    }});
    group.classList.toggle("hidden", visibleChildren === 0);
  }});
  document.querySelectorAll("#storePanel .store-panel-card").forEach(card => {{
    card.classList.toggle("hidden", !matchesItem(card, search));
  }});
  sortTimeline();
  updateResultCount();
  setupScrollIndicators();
}}

function setViewMode(mode) {{
  currentView = mode === "store" || mode === "list" ? mode : "timeline";
  document.getElementById("timelineView").classList.toggle("hidden", currentView !== "timeline");
  document.getElementById("storeView").classList.toggle("hidden", currentView !== "store");
  document.getElementById("storeListView").classList.toggle("hidden", currentView !== "list");
  document.getElementById("timelineViewButton").classList.toggle("active", currentView === "timeline");
  document.getElementById("storeViewButton").classList.toggle("active", currentView === "store");
  document.getElementById("storeListViewButton").classList.toggle("active", currentView === "list");
  const storePanel = document.getElementById("storePanel");
  if (storePanel) storePanel.setAttribute("aria-hidden", currentView === "list" ? "false" : "true");
  updateStoreRangeButtons();
  updateStoreRangeVisibility();
  applyFilters();
  requestAnimationFrame(() => setupScrollIndicators());
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
  document.getElementById("storeListViewButton").addEventListener("click", () => setViewMode("list"));
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
  bindLandscapeImages();
  setupScrollIndicators();
  syncTypeButtons();
  syncBrandButtons();
  renderSelectedBrands();
  filterBrandOptions();
  currentStoreRange = "week";
  updateStoreRangeButtons();
  updateStoreRangeVisibility();
  applyFilters();
  setViewMode("store");
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
    timeline_cards_html = ""

    for post in merge_posts_by_tweet(posts):
        image_urls = post.get("image_urls", [])
        if not image_urls:
            continue

        display_type = post.get("display_type", infer_display_type(post))
        type_label = post.get("display_type_label") or short_type_label(display_type)
        checked_label = format_update_label(post.get("posted_at") or post.get("collected_at", updated_at))
        image_count = len(image_urls)
        image_buttons = []
        first_media_id = ""

        for image_index, image_url in enumerate(image_urls):
            media_id = f'{post.get("source_id", "post")}_{post.get("status_id", 0)}_{image_index}'
            if not first_media_id:
                first_media_id = media_id

            media_items[media_id] = {
                "image_url": image_url,
                "tweet_url": post["tweet_url"],
                "summary": short_summary(post.get("summary", "")),
                "type_label": type_label,
            }

            image_buttons.append(f"""
    <button class="timeline-image" type="button" onclick="openMedia('{h(media_id)}')">
      <img src="{h(image_url)}" alt="{h(shop["shop_name"])}の買取表画像 {image_index + 1}" loading="lazy" decoding="async">
      <span class="zoom-badge">拡大</span>
      <span class="image-count">画像 {image_index + 1} / {image_count}</span>
      <span class="landscape-hint">横スクロールで確認</span>
    </button>
""")

        timeline_cards_html += f"""
<article class="timeline-post store-timeline-post">
  <div class="timeline-head">
    <div class="timeline-store">{h(shop["shop_name"])}</div>
    <div class="timeline-meta">確認：{h(checked_label)}<span class="timeline-type">　{h(short_type_label(type_label))}</span></div>
  </div>

  <div class="timeline-images">
{''.join(image_buttons)}
  </div>

  <div class="timeline-actions">
    <button type="button" onclick="openMedia('{h(first_media_id)}')">拡大</button>
    <a href="{h(post["tweet_url"])}" target="_blank" rel="noopener noreferrer">Xで開く</a>
  </div>
</article>
"""

    sections_html = f"""
<section class="image-section store-timeline-section">
  <h2>店舗タイムライン</h2>
  <p class="section-note">この店舗の買取投稿を新しい順に表示しています。</p>
  <div class="timeline-list store-timeline-list">
    {timeline_cards_html if timeline_cards_html else '<div class="no-result">該当する買取投稿はありません。<br>条件を変更してください。</div>'}
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
    store_timeline_css = ""

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

  {store_timeline_css}

  <main class="store-layout">
    <div class="store-header">
      <h1 class="store-title">{h(shop["shop_name"])}</h1>
      <div class="store-sub">{h(shop["brand"])} / {h(shop["area"])}</div>
      <p class="area-description">
        この店舗の買取投稿を時系列で表示しています。
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

    <div class="modal-image-wrap" id="modalImageWrap">
      <img class="modal-image" id="modalImage" src="" alt="買取表画像">
      <span class="landscape-hint">横スクロールで確認</span>
    </div>

    <div class="modal-summary" id="modalSummary"></div>

    <div class="modal-actions">
      <a id="modalImageLink" href="#" target="_blank" rel="noopener noreferrer">画像だけ開く</a>
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

function getHighResImageUrl(url) {{
  if (!url || !url.includes("pbs.twimg.com/media/")) return url;
  try {{
    const parsed = new URL(url, window.location.href);
    parsed.searchParams.set("name", "orig");
    return parsed.toString();
  }} catch (e) {{
    return url
      .replace("name=small", "name=orig")
      .replace("name=medium", "name=orig")
      .replace("name=large", "name=orig");
  }}
}}

function upgradeImageElement(img) {{
  if (!img) return "";
  const highResUrl = getHighResImageUrl(img.getAttribute("src") || img.src);
  if (highResUrl && highResUrl !== img.src) img.src = highResUrl;
  return highResUrl;
}}

function markLandscapeImage(img) {{
  if (!img || !img.naturalWidth || !img.naturalHeight) return;
  const ratio = img.naturalWidth / img.naturalHeight;
  const target = img.closest(".timeline-image, .image-card, .modal-image-wrap");
  if (!target) return;
  const isLandscape = ratio >= 1.35;
  target.classList.toggle("is-landscape", isLandscape);
  if (isLandscape) renderLandscapeView(target, img);
  else {{
    target.querySelector(".landscape-split")?.remove();
    target.querySelector(".landscape-mode-switch")?.remove();
    target.classList.remove("landscape-mode-original", "landscape-mode-half", "landscape-mode-quarter");
  }}
  setupScrollIndicators(target);
}}

function getLandscapeMode() {{
  const saved = localStorage.getItem("cardradarLandscapeMode");
  return ["original", "half", "quarter"].includes(saved) ? saved : "half";
}}

function setLandscapeMode(mode) {{
  const nextMode = ["original", "half", "quarter"].includes(mode) ? mode : "half";
  localStorage.setItem("cardradarLandscapeMode", nextMode);
  document.querySelectorAll(".is-landscape").forEach(target => {{
    const img = target.querySelector(":scope > img, :scope > .modal-image");
    if (img) renderLandscapeView(target, img);
  }});
  setupScrollIndicators();
}}

function renderLandscapeModeSwitch(target, mode) {{
  let controls = target.querySelector(".landscape-mode-switch");
  if (!controls) {{
    controls = document.createElement("span");
    controls.className = "landscape-mode-switch";
    target.appendChild(controls);
  }}
  controls.innerHTML = ["original", "half", "quarter"].map(item => {{
    const labels = {{ original: "元画像", half: "縦1/2", quarter: "縦横1/4" }};
    return `<span class="landscape-mode-button ${{item === mode ? "is-active" : ""}}" role="button" tabindex="0" data-landscape-mode="${{item}}">${{labels[item]}}</span>`;
  }}).join("");
  controls.querySelectorAll(".landscape-mode-button").forEach(button => {{
    const activate = event => {{
      event.preventDefault();
      event.stopPropagation();
      setLandscapeMode(button.dataset.landscapeMode);
    }};
    button.addEventListener("click", activate);
    button.addEventListener("keydown", event => {{
      if (event.key === "Enter" || event.key === " ") activate(event);
    }});
  }});
}}

function renderLandscapeView(target, img) {{
  const mode = getLandscapeMode();
  const ratio = img.naturalWidth && img.naturalHeight ? img.naturalWidth / img.naturalHeight : 1.6;
  const sourceUrl = getHighResImageUrl(img.currentSrc || img.src);
  target.classList.toggle("landscape-mode-original", mode === "original");
  target.classList.toggle("landscape-mode-half", mode === "half");
  target.classList.toggle("landscape-mode-quarter", mode === "quarter");
  renderLandscapeModeSwitch(target, mode);
  let split = target.querySelector(".landscape-split");
  if (!split) {{
    split = document.createElement("div");
    split.className = "landscape-split";
    img.insertAdjacentElement("afterend", split);
  }}
  if (mode === "original") {{
    split.innerHTML = "";
    return;
  }}
  if (mode === "quarter") {{
    split.style.setProperty("--landscape-panel-ratio", ratio.toFixed(4));
    split.innerHTML = `
    <div class="landscape-slice is-top-left">
      <span class="landscape-slice-label">左上</span>
      <span class="landscape-slice-frame"><img src="${{sourceUrl}}" alt=""></span>
    </div>
    <div class="landscape-slice is-top-right">
      <span class="landscape-slice-label">右上</span>
      <span class="landscape-slice-frame"><img src="${{sourceUrl}}" alt=""></span>
    </div>
    <div class="landscape-slice is-bottom-left">
      <span class="landscape-slice-label">左下</span>
      <span class="landscape-slice-frame"><img src="${{sourceUrl}}" alt=""></span>
    </div>
    <div class="landscape-slice is-bottom-right">
      <span class="landscape-slice-label">右下</span>
      <span class="landscape-slice-frame"><img src="${{sourceUrl}}" alt=""></span>
    </div>
  `;
    return;
  }}
  split.style.removeProperty("--landscape-panel-ratio");
  split.innerHTML = `
    <div class="landscape-slice is-left">
      <span class="landscape-slice-label">左半分</span>
      <span class="landscape-slice-frame"><img src="${{sourceUrl}}" alt=""></span>
    </div>
    <div class="landscape-slice is-right">
      <span class="landscape-slice-label">右半分</span>
      <span class="landscape-slice-frame"><img src="${{sourceUrl}}" alt=""></span>
    </div>
  `;
}}

function bindLandscapeImages(root = document) {{
  root.querySelectorAll(".timeline-image img, .image-card img").forEach(img => {{
    upgradeImageElement(img);
    img.addEventListener("load", () => markLandscapeImage(img));
    if (img.complete) markLandscapeImage(img);
  }});
}}

function getScrollIndicatorHost(el) {{
  if (el.matches(".store-post-strip, .store-post-image-list")) return el.parentElement || el;
  return el;
}}

function ensureScrollIndicator(el) {{
  const host = getScrollIndicatorHost(el);
  let indicator = el.dataset.scrollIndicatorId
    ? document.getElementById(el.dataset.scrollIndicatorId)
    : null;
  if (!indicator) {{
    indicator = document.createElement("span");
    indicator.className = "scroll-progress";
    indicator.id = `scrollIndicator_${{Math.random().toString(36).slice(2)}}`;
    el.dataset.scrollIndicatorId = indicator.id;
    if (el.matches(".store-post-strip, .store-post-image-list")) {{
      el.insertAdjacentElement("afterend", indicator);
    }} else {{
      host.appendChild(indicator);
    }}
  }}
  return indicator;
}}

function updateScrollIndicator(el) {{
  if (!el || !el.isConnected) return;
  const maxScroll = Math.max(0, el.scrollWidth - el.clientWidth);
  const canScroll = maxScroll > 4;
  el.classList.toggle("scroll-aware", canScroll);
  el.classList.toggle("can-scroll-left", canScroll && el.scrollLeft > 4);
  el.classList.toggle("can-scroll-right", canScroll && el.scrollLeft < maxScroll - 4);
  const indicator = ensureScrollIndicator(el);
  indicator.classList.toggle("is-visible", canScroll);
  if (!canScroll) return;
  const total = Math.max(2, Math.ceil(el.scrollWidth / Math.max(el.clientWidth, 1)));
  const current = Math.min(total, Math.max(1, Math.round((el.scrollLeft / Math.max(maxScroll, 1)) * (total - 1)) + 1));
  indicator.textContent = `${{current}} / ${{total}}`;
}}

function setupScrollIndicators(root = document) {{
  const scope = root instanceof Element ? root : document;
  const targets = new Set();
  if (scope.matches?.(".store-post-strip, .store-post-image-list, .timeline-image.is-landscape, .image-card.is-landscape, .modal-image-wrap.is-landscape, .landscape-split")) targets.add(scope);
  scope.querySelectorAll?.(".store-post-strip, .store-post-image-list, .timeline-image.is-landscape, .image-card.is-landscape, .modal-image-wrap.is-landscape, .landscape-split").forEach(el => targets.add(el));
  targets.forEach(el => {{
    if (!el.dataset.scrollAwareBound) {{
      el.dataset.scrollAwareBound = "1";
      let ticking = false;
      el.addEventListener("scroll", () => {{
        if (ticking) return;
        ticking = true;
        requestAnimationFrame(() => {{
          ticking = false;
          updateScrollIndicator(el);
        }});
      }}, {{ passive: true }});
    }}
    requestAnimationFrame(() => updateScrollIndicator(el));
  }});
}}

function openMedia(id) {{
  const item = MEDIA_ITEMS[id];

  if (!item) return;

  currentTweetUrl = item.tweet_url;

  const modalImage = document.getElementById("modalImage");
  const modalWrap = document.getElementById("modalImageWrap");
  const imageUrl = getHighResImageUrl(item.image_url);
  if (modalWrap) modalWrap.classList.remove("is-landscape");
  modalImage.src = imageUrl;
  modalImage.onload = () => markLandscapeImage(modalImage);
  if (modalImage.complete) markLandscapeImage(modalImage);
  document.getElementById("modalSummary").textContent = item.summary;
  document.getElementById("modalImageLink").href = imageUrl;
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

document.addEventListener("DOMContentLoaded", () => {{
  bindLandscapeImages();
  setupScrollIndicators();
}});
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
    from playwright.sync_api import sync_playwright

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
    overall_log = {
        "target_sources": len(target_sources),
        "success_sources": 0,
        "failed_sources": 0,
        "adopted_posts": 0,
        "kept_previous_posts": 0,
        "exclude_counts": {},
    }

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
            source_log = {
                "url": source["url"],
                "article_status": "未実行",
                "article_count": 0,
                "target_passed": 0,
                "with_images": 0,
                "adopted": 0,
                "exclude_counts": {
                    "status URLなし": 0,
                    "重複": 0,
                    "ポケカ外": 0,
                    "買取表ではない": 0,
                    "お知らせ系": 0,
                    "NGワード": 0,
                    "画像なし": 0,
                    "古すぎる": 0,
                },
            }

            try:
                print("URL:", source_log["url"])
                page.goto(source_log["url"], wait_until="domcontentloaded", timeout=60000)
                time.sleep(initial_wait)

                page.wait_for_selector("article", timeout=30000)
                source_log["article_status"] = "成功"

                for _ in range(scroll_count):
                    page.mouse.wheel(0, 1400)
                    time.sleep(scroll_wait)

                tweets = page.locator("article")
                count = tweets.count()
                source_log["article_count"] = count

                print("検出article数:", count)

                for i in range(min(count, check_limit)):
                    tweet = tweets.nth(i)

                    text = tweet.inner_text()
                    url = get_status_url(tweet)

                    if not url:
                        source_log["exclude_counts"]["status URLなし"] += 1
                        continue

                    if url in seen_urls:
                        source_log["exclude_counts"]["重複"] += 1
                        continue

                    if source.get("shop_slug") == "cardshop-art":
                        is_target = is_art_store_target_post(text)
                    else:
                        is_target = is_target_post(text, source["source_type"])

                    if not is_target:
                        reason = target_exclusion_reason(text)
                        source_log["exclude_counts"][reason] = source_log["exclude_counts"].get(reason, 0) + 1
                        print(f"[除外] {source['shop_name']} source={source['source_type']} display=- date=- reason={reason}")
                        continue
                    source_log["target_passed"] += 1

                    image_urls = get_image_urls(tweet)

                    if not image_urls:
                        source_log["exclude_counts"]["画像なし"] += 1
                        print(f"[除外] {source['shop_name']} source={source['source_type']} display=- date=- reason=no image")
                        continue
                    source_log["with_images"] += 1

                    seen_urls.add(url)
                    posted_at = get_posted_at(tweet)
                    posted_date_jst = posted_date_from_values(posted_at, updated_at)
                    text_for_class = classification_text_for_post({"full_text": text}, source)
                    display_type, reason = classify_display_type(text_for_class, source["source_type"])

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
                adopted_keys = {post_identity(post) for post in posts}
                source_log["exclude_counts"]["古すぎる"] = sum(1 for post in candidates if post_identity(post) not in adopted_keys)
                source_log["adopted"] = len(posts)
                print(f"[保存範囲] {source['shop_name']} {source['source_type']} {build_source_selection_log(candidates, posts)}")

                posts_by_source[source["id"]] = posts
                all_data = replace_source_items(all_data, source["id"], posts)
                save_data_items(all_data)

                latest_date = posts[0].get("posted_date_jst", "-") if posts else "-"
                print(f"[最新日] {latest_date}")
                print(f"[採用] {len(posts)}件")
                for post in posts:
                    print(f"[分類] {post['shop_name']} source={post['source_type']} display={post['display_type']} date={post.get('posted_date_jst') or '-'} reason={post.get('classify_reason') or '-'}")
                overall_log["success_sources"] += 1
                overall_log["adopted_posts"] += len(posts)
                for reason, value in source_log["exclude_counts"].items():
                    overall_log["exclude_counts"][reason] = overall_log["exclude_counts"].get(reason, 0) + value
                print("---- source summary ----")
                print("article取得:", source_log["article_status"])
                print("候補article数:", source_log["article_count"])
                print("is_target通過:", source_log["target_passed"])
                print("画像あり:", source_log["with_images"])
                print("採用:", source_log["adopted"])
                print("除外:")
                for reason, value in source_log["exclude_counts"].items():
                    print(f"  {reason}: {value}")

            except Exception as e:
                source_log["article_status"] = "失敗"
                previous_count = len(posts_by_source.get(source["id"], []))
                overall_log["failed_sources"] += 1
                overall_log["kept_previous_posts"] += previous_count
                print(f"[失敗] {source['id']} reason={e}")
                print("URL:", source_log["url"])
                print("article取得: 失敗")
                print("失敗理由:", type(e).__name__)
                try:
                    print("current_url:", page.url)
                    print("page_title:", page.title())
                except Exception as page_error:
                    print("page_info_error:", page_error)
                print(f"前回data.json: 残す ({previous_count}件)")
                print("前回data.jsonのデータを残します")

        browser.close()

    final_posts_by_source = posts_by_source_from_data(all_data)
    print("")
    print("================================")
    print("取得サマリー")
    print("================================")
    print(f"対象source数: {overall_log['target_sources']}")
    print(f"成功source数: {overall_log['success_sources']}")
    print(f"失敗source数: {overall_log['failed_sources']}")
    print(f"新規採用: {overall_log['adopted_posts']}")
    print(f"前回保持: {overall_log['kept_previous_posts']}")
    print(f"ポケカ外として除外: {count_non_pokemon_exclusions(final_posts_by_source)}")
    print(f"お知らせ系として除外: {count_notice_exclusions(final_posts_by_source)}")
    print("除外理由:")
    for reason, value in overall_log["exclude_counts"].items():
        print(f"  {reason}: {value}")
    print("================================")

    return posts_by_source_from_data(all_data), dedupe_data_items(all_data), updated_at


# =========================
# ファイル保存
# =========================

def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def build_all_pages(posts_by_source, updated_at):
    excluded_count = count_non_pokemon_exclusions(posts_by_source)
    notice_excluded_count = count_notice_exclusions(posts_by_source)
    area_timeline_posts = get_timeline_posts(posts_by_source, "osaka-nihonbashi")
    _, timeline_meta = select_timeline_posts_with_fallback(area_timeline_posts)
    print(f"ポケカ外として除外：{excluded_count}件")
    print(f"お知らせ系として除外：{notice_excluded_count}件")
    print(f"最新日投稿数：{timeline_meta.get('latest_count', 0)}件")
    print(f"補完表示：{'あり' if timeline_meta.get('fallback_used') else 'なし'}")
    print(f"補完後の表示投稿数：{timeline_meta.get('selected_count', 0)}件")

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




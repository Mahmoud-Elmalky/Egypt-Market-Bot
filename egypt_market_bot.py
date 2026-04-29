import asyncio
import json
import logging
import math
import os
import sys
from datetime import datetime

import requests
import yfinance as yf
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from telegram import Bot
    from telegram.error import TelegramError
except ImportError:
    print("\nError: python-telegram-bot is not installed.")
    sys.exit(1)

# Securely load token from .env file
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "@Egy_GoldPrice")

if not TELEGRAM_BOT_TOKEN:
    print("\nError: TELEGRAM_BOT_TOKEN is missing in .env file.")
    sys.exit(1)

CACHE_FILE = "last_prices.json"
UPDATE_INTERVAL_SECONDS = 7200
RETRY_DELAY_SECONDS = 60


logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def save_cache(data: dict) -> None:
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"Failed to save cache: {e}")


def load_cache() -> dict | None:
    if not os.path.exists(CACHE_FILE):
        return None
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


SCRAPE_URL = "https://goldbullioneg.com/"
SCRAPE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/91.0.4472.124 Safari/537.36"
    )
}

GOLD_ROW_MAP = {
    "عيار 24": "g24",
    "عيار 21": "g21",
    "عيار 18": "g18",
    "الجنيه الذهب": "pound",
    "الأونصة": "oz_usd",
    "الدولار": "usd_sagha",
}

YFINANCE_TICKERS = [
    "EGP=X", "EURUSD=X", "GBPUSD=X", "JPY=X", "RUB=X",
    "CNY=X", "SAR=X", "AED=X", "KWD=X", "^CASE30", "SI=F",
]

INVERSE_CURRENCY_TICKERS = {
    "SAR": "SAR=X",
    "AED": "AED=X",
    "KWD": "KWD=X",
    "CNY": "CNY=X",
    "JPY": "JPY=X",
    "RUB": "RUB=X",
}


def _extract_cell_value(row) -> float | None:
    try:
        cell = row.find("td", class_="num")
        if cell and cell.has_attr("data-val"):
            return float(cell["data-val"])
    except (ValueError, TypeError):
        pass
    return None


def scrape_gold_prices() -> dict | None:
    try:
        response = requests.get(SCRAPE_URL, headers=SCRAPE_HEADERS, timeout=15)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.content, "html.parser")
        scraped: dict[str, float] = {}

        for row in soup.find_all("tr"):
            text = row.get_text()
            for keyword, key in GOLD_ROW_MAP.items():
                if keyword in text:
                    value = _extract_cell_value(row)
                    if value is not None:
                        scraped[key] = value
                    break

        return scraped if scraped.get("g21") else None

    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        return None


def _get_last_valid_close(df, ticker: str) -> float:
    try:
        series = df[ticker].dropna()
        if not series.empty:
            return float(series.iloc[-1])
    except Exception:
        pass
    return 0.0


async def get_market_data() -> dict:
    data = {
        "currencies": {},
        "gold": {},
        "egx30": 0.0,
        "silver_gram": 0.0,
        "source": "Live",
    }

    scraped = scrape_gold_prices()
    if scraped:
        data["gold"] = scraped
    else:
        cached = load_cache()
        if cached and "gold" in cached:
            data["gold"] = cached["gold"]
            data["source"] = "Cached"
        else:
            data["source"] = "Theoretical"

    try:
        df = yf.download(YFINANCE_TICKERS, period="5d", progress=False)["Close"]
        usd_egp = _get_last_valid_close(df, "EGP=X")

        if usd_egp > 0:
            if "usd_sagha" not in data["gold"]:
                data["gold"]["usd_sagha"] = usd_egp

            data["currencies"]["USD"] = usd_egp
            data["currencies"]["EUR"] = _get_last_valid_close(df, "EURUSD=X") * usd_egp
            data["currencies"]["GBP"] = _get_last_valid_close(df, "GBPUSD=X") * usd_egp

            for currency_code, ticker in INVERSE_CURRENCY_TICKERS.items():
                rate = _get_last_valid_close(df, ticker)
                data["currencies"][currency_code] = (usd_egp / rate) if rate > 0 else 0.0

            silver_usd = _get_last_valid_close(df, "SI=F")
            data["silver_gram"] = (silver_usd * usd_egp) / 31.1035
            data["egx30"] = _get_last_valid_close(df, "^CASE30")

    except Exception as e:
        logger.error(f"yfinance fetch failed: {e}")
        cached = load_cache()
        if cached and "currencies" in cached:
            data["currencies"] = cached["currencies"]
            data["egx30"] = cached.get("egx30", 0.0)

    if data["source"] == "Live":
        save_cache(data)

    return data


def _sanitize(value) -> float:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return 0.0
    return value


def _fmt_int(value) -> str:
    value = _sanitize(value)
    return f"{value:,.0f}" if value > 0 else "---"


def _fmt_float(value) -> str:
    value = _sanitize(value)
    return f"{value:,.2f}" if value > 0 else "0.00"


def format_message(data: dict) -> str | None:
    if not data:
        return None

    gold = data.get("gold", {})
    currencies = data.get("currencies", {})

    local_ounce = "---"
    g24 = _sanitize(gold.get("g24"))
    if g24 > 0:
        local_ounce = f"{g24 * 31.1035:,.0f}"

    status = " (⚠️ Last recorded update)" if data.get("source") != "Live" else ""

    return f"""
📌 اسعار الذهب الأن{status}

💍 عيار_18_       {_fmt_int(gold.get('g18'))} ج.م
💍 عيار_21_       {_fmt_int(gold.get('g21'))} ج.م
💍 عيار_24_      {_fmt_int(gold.get('g24'))} ج.م

💎 سعر الجنيه الذهب: {_fmt_int(gold.get('pound'))} ج.م
⏩ سعر الأونصة (الأوقية): {local_ounce} ج.م
⏩ سعر الاونصة عالميا (الشاشة): {_fmt_int(gold.get('oz_usd'))}$
🕛 السعر المحلي الفضة: {_fmt_float(data.get('silver_gram'))} ج.م
🔔 الأسعار غير شامله الضريبة والمصنعية
ـــــــــــــــــــــــــــــــــــــــــــــــــــ
🏛️ اسعار العملات الأن

🇺🇸 الدولار= {_fmt_float(currencies.get('USD'))} ج.م
🇪🇺 اليورو= {_fmt_float(currencies.get('EUR'))} ج.م
🇬🇧 الجنيه الاسترليني= {_fmt_float(currencies.get('GBP'))} ج.م
🇯🇵 الين الياباني= {_fmt_float(currencies.get('JPY'))} ج.م
🇷🇺 الروبل الروسي= {_fmt_float(currencies.get('RUB'))} ج.م
🇨🇳 اليوان الصيني= {_fmt_float(currencies.get('CNY'))} ج.م
🇸🇦 الريال السعودي= {_fmt_float(currencies.get('SAR'))} ج.م
🇰🇼 الدينار الكويتي= {_fmt_float(currencies.get('KWD'))} ج.م
🇦🇪  الدرهم الإماراتي= {_fmt_float(currencies.get('AED'))} ج.م
ـــــــــــــــــــــــــــــــــــــــــــــــــــ
مؤشر EGX30 بالبورصة المصرية= {_fmt_float(data.get('egx30'))} نقطة


#اقتصاد #مصر #سعر_الذهب #سعر_الفضة #سعر_الدولار #EGX30 #استثمار #دولار #الذهب #فضة #اسعار_العملات
""".strip()


async def send_updates(bot: Bot) -> None:
    logger.info(f"Connected. Publishing to: {TELEGRAM_CHANNEL_ID}")
    while True:
        try:
            logger.info("Fetching latest market data...")
            data = await get_market_data()
            if data:
                message = format_message(data)
                if message:
                    await bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=message)
                    logger.info("Message sent successfully.")
            else:
                logger.warning("No data available.")
            await asyncio.sleep(UPDATE_INTERVAL_SECONDS)
        except Exception as e:
            logger.error(f"Error during update cycle: {e}")
            await asyncio.sleep(RETRY_DELAY_SECONDS)


async def main() -> None:
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    await send_updates(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBot stopped.")

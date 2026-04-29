# Egypt Global Market Rates Bot

### Automated Financial Data Tracker for Telegram

A robust, fully automated Python system that aggregates and publishes real-time financial data to Telegram channels. This project focuses on high-frequency tracking of the Egyptian gold market, global fiat currencies, and the EGX30 stock index.

---

### Key Features

- **Multi-Source Scraping:** Fetches local gold prices from Egyptian bullion markets while integrating global data via Yahoo Finance.
- **Dynamic Currency Conversion:** Automatically calculates exchange rates for major currencies against the Egyptian Pound using real-time USD/EGP values.
- **Reliable Caching Logic:** Implements a local JSON-based fail-safe mechanism to broadcast the last known valid prices if sources are temporarily offline.
- **Asynchronous Loop:** Designed with `asyncio` for non-blocking execution, ensuring updates are pushed exactly every 2 hours without manual intervention.

---

### Tech Stack

| Component | Technology |
| :--- | :--- |
| Core Language | Python 3.10+ |
| Framework | python-telegram-bot (v20+) |
| Data APIs | yfinance |
| Scraping | requests, BeautifulSoup4 |
| Security | python-dotenv |

---

### Output Format Preview

```text
📌 اسعار الذهب الأن

💍 عيار_18_       5,871 ج.م
💍 عيار_21_       6,850 ج.م
💍 عيار_24_      7,829 ج.م

💎 سعر الجنيه الذهب: 54,800 ج.م
⏩ سعر الأونصة (الأوقية): 243,509 ج.م
⏩ سعر الاونصة عالميا (الشاشة): 4,533$
🕛 السعر المحلي الفضة: 121.75 ج.م
🔔 الأسعار غير شامله الضريبة والمصنعية
ـــــــــــــــــــــــــــــــــــــــــــــــــــ
🏛️ اسعار العملات الأن

🇺🇸 الدولار= 52.95 ج.م
🇪🇺 اليورو= 61.86 ج.م
🇬🇧 الجنيه الاسترليني= 71.37 ج.م
🇸🇦 الريال السعودي= 14.12 ج.م
🇦🇪  الدرهم الإماراتي= 14.42 ج.م
ـــــــــــــــــــــــــــــــــــــــــــــــــــ
مؤشر EGX30 بالبورصة المصرية= 52,383.10 نقطة
```
### Live Demo

You can monitor the bot's automated updates and real-time market reports through the official Telegram channel:
[Join Egypt Gold Price Channel](https://t.me/Egy_GoldPrice)

### Installation & Setup Guide

Follow these steps to deploy the bot on your local machine or a server:

#### 1. Clone the Repository
Start by cloning the project files to your local environment:
```bash
git clone [https://github.com/Mahmoud-Elmalky/Egypt-Market-Bot.git](https://github.com/Mahmoud-Elmalky/Egypt-Market-Bot.git)
cd Egypt-Market-Bot
```
#### **2. Create a Virtual Environment (Recommended)**

Isolate your project dependencies to avoid conflicts:

```bash

python -m venv venv  
# For Windows:  
venv\Scripts\activate  
# For Linux/Mac:  
source venv/bin/activate
```
#### **3. Install Required Packages**

Install the necessary libraries listed in the requirements file:

```bash
pip install -r requirements.txt
```

#### **4. Obtain Telegram Credentials**

* Message **@BotFather** on Telegram to create a new bot and receive your **API Token**.  
* Create a Public or Private Channel and add your bot as an **Administrator** with permission to post messages.  
* Get your Channel ID (e.g., `@YourChannelName`).

#### **5. Configure Environment Variables**

Create a file named `.env` in the root directory (the .gitignore will prevent this file from being uploaded). Add your credentials:

```Code snippet

TELEGRAM_BOT_TOKEN=your_token_here  
TELEGRAM_CHANNEL_ID=@your_channel_username
```

#### **6. Run the Application**

Start the bot to begin the automated 2-hour update cycle:

```Bash
python egypt_market_bot.py
```

#### **7. Logging & Persistence**

The bot logs activity directly to the terminal. It also creates a `last_prices.json` file automatically to manage data persistence across runs.

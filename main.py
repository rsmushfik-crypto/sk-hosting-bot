import os, json, sys, subprocess, shutil
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("8762948576:AAFEZY31Wg2Qh0ELnCJb6iP0sBob7UseoHQ")
ADMIN_ID = int(os.getenv("8933985337", "0"))
DB_FILE = "database.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "processes": {}}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(d):
    with open(DB_FILE, "w") as f:
        json.dump(d, f, indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 SK Free Hosting Bot\n\n"
        "✅ Python ফাইল পাঠাও আমি হোস্ট করে দেব\n"
        "📌 শুধু.py ফাইল সাপোর্ট করবে\n\n"
        "▶️ /run - বট রান করো\n"
        "⏹️ /stop - বট বন্ধ করো\n"
        "📁 /mybots - আমার ফাইল দেখো\n"
        "🆘 /help"
    )

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    file = update.message.document
    if not file.file_name.endswith('.py'):
        await update.message.reply_text("❌ শুধু.py ফাইল পাঠাও। যেমন bot.py, main.py")
        return

    os.makedirs(f"bots/{user_id}", exist_ok=True)
    tg_file = await context.bot.get_file(file.file_id)
    save_path = f"bots/{user_id}/{file.file_name}"
    await tg_file.download_to_drive(save_path)

    db = load_db()
    db["users"][user_id] = db["users"].get(user_id, {"files": []})
    if file.file_name not in db["users"][user_id]["files"]:
        db["users"][user_id]["files"].append(file.file_name)
    save_db(db)

    await update.message.reply_text(f"✅ Saved: `{file.file_name}`\nএখন /run লিখে `{file.file_name}` রান করো", parse_mode="Markdown")

async def handle_code_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # যদি ইউজার সরাসরি কোড পেস্ট করে
    text = update.message.text
    if "import" in text and "def" in text or "bot.run" in text:
        user_id = str(update.effective_user.id)
        os.makedirs(f"bots/{user_id}", exist_ok=True)
        save_path = f"bots/{user_id}/main.py"
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(text)
        await update.message.reply_text("✅ তোমার কোড main.py হিসেবে সেভ করেছি। /run দিয়ে রান করো")

async def run_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    db = load_db()
    if user_id not in db["users"] or not db["users"][user_id]["files"]:
        await update.message.reply_text("❌ আগে কোনো.py ফাইল পাঠাও")
        return

    # শেষ ফাইলটা রান করবে
    file_name = db["users"][user_id]["files"][-1]
    if context.args:
        file_name = context.args[0]

    file_path = f"bots/{user_id}/{file_name}"
    if not os.path.exists(file_path):
        await update.message.reply_text("❌ ফাইল পাওয়া যায়নি")
        return

    try:
        # আগের প্রসেস বন্ধ করা
        if user_id in db["processes"]:
            try:
                os.kill(db["processes"][user_id], 9)
            except:
                pass

        proc = subprocess.Popen([sys.executable, file_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        db["processes"][user_id] = proc.pid
        save_db(db)
        await update.message.reply_text(f"🚀 রানিং: `{file_name}`\nPID: {proc.pid}\n⏹️ /stop দিয়ে বন্ধ করতে পারবে", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def stop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    db = load_db()
    if user_id in db["processes"]:
        try:
            os.kill(db["processes"][user_id], 9)
            del db["processes"][user_id]
            save_db(db)
            await update.message.reply_text("⏹️ তোমার বট বন্ধ করে দেওয়া হয়েছে")
        except Exception as e:
            await update.message.reply_text(f"Error: {e}")
    else:
        await update.message.reply_text("❌ তোমার কোনো বট রানিং নেই")

# ADMIN PANEL
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id!= ADMIN_ID:
        return
    db = load_db()
    await update.message.reply_text(f"👑 ADMIN PANEL\n\nUsers: {len(db['users'])}\nRunning: {len(db['processes'])}\n\n/stats - Details\n/broadcast - সবাইকে মেসেজ\n/stopall - সব বন্ধ")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("run", run_cmd))
    app.add_handler(CommandHandler("stop", stop_cmd))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_code_text))
    print("Bot Started...")
    app.run_polling()

if __name__ == "__main__":
    main()

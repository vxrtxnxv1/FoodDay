import json
import os
import random
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

TOKEN = os.getenv("TOKEN")
DATA_FILE = "dishes.json"

ADD_DISH = 1

def load_dishes():
    if not os.path.exists(DATA_FILE):
        return {"all": [], "used": []}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_dishes(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Что приготовить сегодня?", "Добавить блюдо"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Что сегодня на обед?", reply_markup=reply_markup)

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    data = load_dishes()

    if text == "Что приготовить сегодня?":
        available = list(set(data["all"]) - set(data["used"]))
        if not available:
            data["used"] = []
            available = data["all"]
        dish = random.choice(available)
        data["used"].append(dish)
        save_dishes(data)
        await update.message.reply_text(f"Сегодняшнее предложение:

**{dish}**", parse_mode="Markdown")
    elif text == "Добавить блюдо":
        await update.message.reply_text("Напиши новое блюдо:")
        return ADD_DISH

    return ConversationHandler.END

async def add_dish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_dish = update.message.text.strip()
    data = load_dishes()
    if new_dish and new_dish not in data["all"]:
        data["all"].append(new_dish)
        save_dishes(data)
        await update.message.reply_text(f"Блюдо **{new_dish}** добавлено!", parse_mode="Markdown")
    else:
        await update.message.reply_text("Такое блюдо уже есть или оно некорректное.")
    return ConversationHandler.END

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)],
        states={ADD_DISH: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_dish)]},
        fallbacks=[],
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.run_polling()
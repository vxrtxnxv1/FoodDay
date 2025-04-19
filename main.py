import json
import os
import random
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
from flask import Flask
from threading import Thread

TOKEN = os.getenv("TOKEN")
DATA_FILE = "dishes.json"
ADD_DISH = 1

# Flask-сервер (для Render / UptimeRobot)
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Бот работает!"

def run_web():
    web_app.run(host="0.0.0.0", port=8080)

Thread(target=run_web).start()

# Работа с блюдами
def load_dishes():
    if not os.path.exists(DATA_FILE):
        return {"all": [], "used": []}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_dishes(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Что приготовить сегодня?", "Добавить блюдо"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Что сегодня на обед?", reply_markup=reply_markup)

# Обработка сообщений
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    data = load_dishes()

    if text == "Что приготовить сегодня?":
        available = list(set(data["all"]) - set(data["used"]))
        if not available:
            data["used"] = []
            available = data["all"]

        if not available:
            await update.message.reply_text("Список блюд пуст. Добавь что-нибудь.")
            return ConversationHandler.END

        dish = random.choice(available)
        data["used"].append(dish)
        save_dishes(data)
        await update.message.reply_text(
            f"Сегодняшнее предложение:\n\n**{dish}**",
            parse_mode="Markdown"
        )

    elif text == "Добавить блюдо":
        await update.message.reply_text("Напиши новое блюдо:")
        return ADD_DISH

    return ConversationHandler.END

# Добавление блюда
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

# Запуск бота
if __name__ == "__main__":
    application = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)],
        states={ADD_DISH: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_dish)]},
        fallbacks=[],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(conv_handler)

    application.run_polling()

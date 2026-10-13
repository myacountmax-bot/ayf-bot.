import os

import json
import random
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, ContextTypes, filters
)

TOKEN = os.environ.get("BOT_TOKEN", "")
ADMIN_IDS = {7114949708}
DATA_FILE = Path.home() / "ayf_data.json"

DEFAULT_DATA = {
    "chance": 0.40,
    "phrases": [
        "Ладно", "Привет", "Пиздец", "Говно бля",
        "Иди нахуй", "Ауф", "Депай в казик",
        "Ауфдроп", "Нукста", "Ауф топ!",
        "Моня топ!", "Эх бля", "Наша база имба", "Ну да"
    ]
}

def load_data():
    try:
        data = json.loads(DATA_FILE.read_text())
        if not isinstance(data.get("phrases"), list):
            raise ValueError("Invalid phrases")
        data["chance"] = max(0, min(1, float(data["chance"])))
        return data
    except (OSError, ValueError, TypeError, KeyError):
        return DEFAULT_DATA.copy()

data = load_data()

def save_data():
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2))

def is_admin(user_id):
    return user_id in ADMIN_IDS

def panel_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Статус", callback_data="status")],
        [
            InlineKeyboardButton("🎲 Шанс ответа", callback_data="chance"),
            InlineKeyboardButton("📝 Фразы", callback_data="phrases")
        ],
        [InlineKeyboardButton("➕ Добавить фразу", callback_data="add")],
        [InlineKeyboardButton("🔙 Закрыть", callback_data="close")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if is_admin(user.id):
        text = (
            "💀 AUF CONTROL SYSTEM\n\n"
            "╭━━━━━━━━━━━━━━━━━━╮\n"
            "   ДОБРО ПОЖАЛОВАТЬ, БОСС\n"
            "╰━━━━━━━━━━━━━━━━━━╯\n\n"
            "⚡ Бот: ayf.bot\n"
            "🟢 Статус: ONLINE\n"
            "👑 Уровень доступа: ВЛАДЕЛЕЦ\n\n"
            "Система готова к управлению.\n"
            "Выберите нужный раздел."
        )
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("⚙️ Админ-панель", callback_data="panel")
        ]])
        await update.message.reply_text(text, reply_markup=keyboard)
    else:
        await update.message.reply_text("Привет! Это Super_ayf бот!")

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Твой Telegram ID: {update.effective_user.id}")

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("Нет доступа.")
        return
    await update.message.reply_text("⚙️ AUF CONTROL SYSTEM", reply_markup=panel_keyboard())

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == "close":
        if is_admin(user_id):
            await query.edit_message_text("Панель закрыта.")
        return

    if not is_admin(user_id):
        await query.answer("Нет доступа!", show_alert=True)
        return

    if query.data == "panel":
        await query.edit_message_text(
            "⚙️ AUF CONTROL SYSTEM\nВыбери действие:",
            reply_markup=panel_keyboard()
        )
    elif query.data == "status":
        await query.edit_message_text(
            f"🟢 Бот запущен\n"
            f"🎲 Шанс ответа: {data['chance'] * 100:.0f}%\n"
            f"📝 Фраз: {len(data['phrases'])}",
            reply_markup=panel_keyboard()
        )
    elif query.data == "chance":
        context.user_data["awaiting"] = "chance"
        await query.edit_message_text(
            "🎲 Отправь шанс ответа числом от 0 до 100.\n"
            "Например: 40"
        )
    elif query.data == "phrases":
        phrases = "\n".join(
            f"{i + 1}. {p}" for i, p in enumerate(data["phrases"])
        )
        if len(phrases) > 3500:
            phrases = phrases[:3500] + "\n..."
        await query.edit_message_text(
            "📝 Фразы бота:\n\n" + (phrases or "Список пуст."),
            reply_markup=panel_keyboard()
        )
    elif query.data == "add":
        context.user_data["awaiting"] = "phrase"
        await query.edit_message_text("➕ Отправь новую фразу одним сообщением.")

async def messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message = update.effective_message
    if not message or not message.text:
        return

    waiting = context.user_data.get("awaiting")
    if is_admin(user_id) and waiting == "chance":
        try:
            value = float(message.text.strip().replace(",", "."))
            if not 0 <= value <= 100:
                raise ValueError
            data["chance"] = value / 100
            save_data()
            context.user_data.pop("awaiting", None)
            await message.reply_text(
                f"✅ Шанс ответа установлен: {value:g}%",
                reply_markup=panel_keyboard()
            )
        except ValueError:
            await message.reply_text("Введи число от 0 до 100.")
        return

    if is_admin(user_id) and waiting == "phrase":
        phrase = message.text.strip()
        if not phrase or len(phrase) > 300:
            await message.reply_text("Фраза должна содержать от 1 до 300 символов.")
            return
        data["phrases"].append(phrase)
        save_data()
        context.user_data.pop("awaiting", None)
        await message.reply_text("✅ Фраза добавлена!", reply_markup=panel_keyboard())
        return

    if message.text.startswith("/"):
        return

    if data["phrases"] and random.random() < data["chance"]:
        await message.reply_text(random.choice(data["phrases"]))

async def errors(update: object, context: ContextTypes.DEFAULT_TYPE):
    print("Ошибка бота:", context.error)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("id", get_id))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, messages))
    app.add_error_handler(errors)
    print("ayf.bot запущен 💀")
    app.run_polling()

if __name__ == "__main__":
    main()

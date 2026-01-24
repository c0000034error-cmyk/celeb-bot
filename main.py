import os
import logging
import asyncio
import random
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from threading import Thread

# ===============================
# 🔐 БЕЗОПАСНОСТЬ
# ===============================
# ❌ НИКАКИХ токенов и айди в коде
# ✅ ВСЁ берётся из Environment Variables (Render)

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

if not BOT_TOKEN:
    raise Exception("❌ BOT_TOKEN не найден")
if not CHANNEL_ID:
    raise Exception("❌ CHANNEL_ID не найден")
if not ADMIN_ID:
    raise Exception("❌ ADMIN_ID не найден")

# ===============================
# 🌐 Flask (чтобы Render не спал)
# ===============================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

Thread(target=run_flask).start()

# ===============================
# ⚙️ BOT
# ===============================
logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

CHANNEL_URL = "https://t.me/celebgifts"
REF_URL = "https://t.me/budabonus_bot?start=8551410557"

USERS_FILE = "users.txt"

# ===============================
# 💾 USERS
# ===============================
def save_user(user_id: int):
    if not os.path.exists(USERS_FILE):
        open(USERS_FILE, "w").close()

    with open(USERS_FILE, "r") as f:
        users = f.read().splitlines()

    if str(user_id) not in users:
        with open(USERS_FILE, "a") as f:
            f.write(str(user_id) + "\n")

# ===============================
# 📢 SUB CHECK
# ===============================
async def is_subscribed(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ("member", "administrator", "creator")
    except:
        return False

# ===============================
# ▶️ START
# ===============================
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    user_id = message.from_user.id
    name = message.from_user.first_name

    save_user(user_id)

    if await is_subscribed(user_id):
        text = (
            f"🌟 <b>С возвращением, {name}!</b>\n\n"
            f"✅ Подписка подтверждена.\n"
            f"Выбери действие 👇"
        )
        keyboard = InlineKeyboardMarkup(row_width=1).add(
            InlineKeyboardButton("🎁 Забрать награды", url=REF_URL),
            InlineKeyboardButton("🎰 Казино (по фану)", callback_data="casino")
        )
        await message.answer(text, reply_markup=keyboard)
    else:
        text = (
            f"👋 <b>Привет, {name}!</b>\n\n"
            f"Чтобы получить доступ, подпишись на канал 👇"
        )
        keyboard = InlineKeyboardMarkup(row_width=1).add(
            InlineKeyboardButton("📢 Подписаться", url=CHANNEL_URL),
            InlineKeyboardButton("✅ Я подписался", callback_data="check_sub")
        )
        await message.answer(text, reply_markup=keyboard)

# ===============================
# ✅ CHECK SUB BUTTON
# ===============================
@dp.callback_query_handler(text="check_sub")
async def check_sub(callback: types.CallbackQuery):
    if await is_subscribed(callback.from_user.id):
        text = (
            "🎉 <b>Подписка подтверждена!</b>\n\n"
            "Теперь доступно:\n"
            "🎁 Награды\n"
            "🎰 Казино"
        )
        keyboard = InlineKeyboardMarkup(row_width=1).add(
            InlineKeyboardButton("🎁 Забрать награды", url=REF_URL),
            InlineKeyboardButton("🎰 Казино (по фану)", callback_data="casino")
        )
        await callback.message.edit_text(text, reply_markup=keyboard)
    else:
        await callback.answer("❌ Ты не подписан на канал", show_alert=True)

# ===============================
# 🎰 CASINO
# ===============================
@dp.callback_query_handler(text="casino")
async def casino(callback: types.CallbackQuery):
    roll = random.randint(1, 100)

    if roll <= 35:
        text = (
            "🎰 <b>КАЗИНО</b>\n\n"
            "🔥 <b>ПОБЕДА!</b>\n"
            "Сегодня удача на твоей стороне 😎"
        )
    else:
        text = (
            "🎰 <b>КАЗИНО</b>\n\n"
            "💀 <b>Проигрыш</b>\n"
            "Попробуй ещё раз 😉"
        )

    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton("🔁 Сыграть ещё раз", callback_data="casino")
    )

    await callback.message.answer(text, reply_markup=keyboard)

# ===============================
# 📢 BROADCAST (ONLY ADMIN)
# ===============================
@dp.message_handler(commands=["broadcast"])
async def broadcast(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    text = message.text.replace("/broadcast", "").strip()
    if not text:
        await message.answer("❌ Напиши текст после команды")
        return

    if not os.path.exists(USERS_FILE):
        await message.answer("❌ Нет пользователей")
        return

    with open(USERS_FILE, "r") as f:
        users = f.read().splitlines()

    sent = 0
    await message.answer(f"📢 Рассылка на {len(users)} пользователей")

    for uid in users:
        try:
            await bot.send_message(uid, text)
            sent += 1
            await asyncio.sleep(0.05)
        except:
            pass

    await message.answer(f"✅ Готово! Отправлено: {sent}")

# ===============================
# 🚀 RUN
# ===============================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)

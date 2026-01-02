import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
from threading import Thread

# --- Настройка Flask (для 24/7) ---
app = Flask('')
@app.route('/')
def home(): return "Бот работает!"

def run(): app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# --- Настройка бота ---
API_TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID') 
ADMIN_ID = os.getenv('ADMIN_ID') # Твой ID из Secrets
CHANNEL_URL = "https://t.me/celebgifts"
REF_URL = "https://t.me/budabonus_bot?start=8551410557" # Твоя рефка

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

# Функция для сохранения ID пользователя в базу (файл)
def save_user(user_id):
    if not os.path.exists("users.txt"):
        open("users.txt", "w").close()

    with open("users.txt", "r") as f:
        users = f.read().splitlines()

    if str(user_id) not in users:
        with open("users.txt", "a") as f:
            f.write(str(user_id) + "\n")

async def check_sub(user_id):
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status != 'left'
    except Exception: return False

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    save_user(message.from_user.id) # Сохраняем юзера для рассылки
    user_name = message.from_user.first_name

    if await check_sub(message.from_user.id):
        text = (
            f"🌟 <b>С возвращением, {user_name}!</b>\n\n"
            f"📝 <b>Инструкция:</b>\n"
            f"1. Нажми кнопку ниже\n"
            f"2. Подпишись на <u>всех</u> спонсоров в открывшемся боте\n"
            f"3. Получи свою награду! 🎁"
        )
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🎁 ЗАБРАТЬ МОИ НАГРАДЫ", url=REF_URL))
        await message.answer(text, reply_markup=markup)
    else:
        text = (f"👋 <b>Привет, {user_name}!</b>\n\nЧтобы получить доступ к подаркам, подпишись на наш канал 👇")
        markup = InlineKeyboardMarkup(row_width=1).add(
            InlineKeyboardButton("📢 Подписаться на канал", url=CHANNEL_URL),
            InlineKeyboardButton("✅ Я подписался, проверить", callback_data="check_subscription")
        )
        await message.answer(text, reply_markup=markup)

@dp.callback_query_handler(text="check_subscription")
async def callback_check(call: types.CallbackQuery):
    if await check_sub(call.from_user.id):
        await call.answer("🔥 Доступ получен!")
        success_text = (
            f"🎉 <b>Проверка пройдена!</b>\n\n"
            f"⚠️ <b>ВАЖНО:</b> После перехода нужно будет <b>подписаться на всех спонсоров</b> для получения награды!"
        )
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🚀 ПЕРЕЙТИ И ПОЛУЧИТЬ", url=REF_URL))
        await call.message.edit_text(success_text, reply_markup=markup)
    else:
        await call.answer("⚠️ Вы не подписаны на канал!", show_alert=True)

# --- БЛОК РАССЫЛКИ ---
@dp.message_handler(commands=['broadcast'])
async def broadcast(message: types.Message):
    # Проверка, что команду пишет админ
    if str(message.from_user.id) != str(ADMIN_ID):
        return

    # Извлекаем текст сообщения (всё, что после /broadcast)
    broadcast_text = message.text.replace("/broadcast", "").strip()

    if not broadcast_text:
        await message.answer("❌ Введи текст рассылки после команды. Пример:\n<code>/broadcast Всем привет!</code>")
        return

    if not os.path.exists("users.txt"):
        await message.answer("❌ База пользователей пуста.")
        return

    with open("users.txt", "r") as f:
        users = f.read().splitlines()

    count = 0
    await message.answer(f"📢 Начинаю рассылку на {len(users)} пользователей...")

    for user_id in users:
        try:
            await bot.send_message(user_id, broadcast_text)
            count += 1
            await asyncio.sleep(0.05) # Защита от спам-фильтра Telegram
        except Exception:
            pass # Если юзер заблокировал бота, просто пропускаем

    await message.answer(f"✅ Рассылка завершена!\nДоставлено: {count} из {len(users)}")

if __name__ == '__main__':
    keep_alive()
    executor.start_polling(dp, skip_updates=True)

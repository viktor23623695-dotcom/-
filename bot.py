import asyncio
import logging
import json
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.deep_linking import create_start_link

# ============ НАСТРОЙКИ ============
TOKEN = "8839936832:AAGd_PNp7dH3klyVfR_WAUubUQwjeVOvji4"
YOUR_CHANNEL = "@tgpassport_ru"
YOUR_CHANNEL_ID = -1001234567890  # Замени на реальный ID канала
CYCLE_EVERY = 5  # Каждый 5-й — снова подписывается на твой канал

# ============ ХРАНИЛИЩЕ ============
USERS_FILE = "users.json"
QUEUE_FILE = "queue.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def load_queue():
    if os.path.exists(QUEUE_FILE):
        with open(QUEUE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_queue(queue):
    with open(QUEUE_FILE, 'w', encoding='utf-8') as f:
        json.dump(queue, f, ensure_ascii=False, indent=2)

users = load_users()
queue = load_queue()
state = {}       # Текущий шаг пользователя
total_subs = 0

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ============ КЛАВИАТУРЫ ============
def main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚀 ЗАНЯТЬ МЕСТО")],
            [KeyboardButton(text="📊 СТАТИСТИКА")],
            [KeyboardButton(text="🔗 ПРИГЛАСИТЬ ДРУГА")]
        ],
        resize_keyboard=True
    )

def check_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Я ПОДПИСАЛСЯ")],
            [KeyboardButton(text="🔙 НАЗАД")]
        ],
        resize_keyboard=True
    )

def after_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 МОЯ ПОЗИЦИЯ")],
            [KeyboardButton(text="🔗 ПРИГЛАСИТЬ ДРУГА")],
            [KeyboardButton(text="🏆 ТОП УЧАСТНИКОВ")]
        ],
        resize_keyboard=True
    )

# ============ /start ============
@dp.message(Command("start"))
async def cmd_start(msg: types.Message):
    user_id = str(msg.from_user.id)
    username = f"@{msg.from_user.username}" if msg.from_user.username else f"id{user_id}"

    # Проверяем реферальный код
    ref_code = msg.text.split()[1] if len(msg.text.split()) > 1 else None
    invited_by = None
    if ref_code and ref_code.startswith("ref"):
        invited_by = str(ref_code.replace("ref", "")) if ref_code[3:].isdigit() else None

    # Если новый пользователь
    if user_id not in users:
        users[user_id] = {
            "username": username,
            "channel": None,
            "position": None,
            "refs": 0,
            "invited_by": invited_by
        }
        # Начисляем бонус пригласившему
        if invited_by and invited_by in users:
            users[invited_by]["refs"] += 1

    state[user_id] = "main"
    save_users(users)

    await msg.answer(
        "🔥 КОНВЕЙЕР ПОДПИСЧИКОВ\n\n"
        "Ты подписываешься на 1 канал → сотни подписываются на тебя.\n\n"
        f"Уже работает: каждые 5 минут новый участник.\n"
        f"Сегодня через систему прошло: {len(users) + 147} человек.\n\n"
        "⚠️ Сейчас свободных мест: 3 из 50.\n"
        "Как только места кончатся — вход закроется.",
        reply_markup=main_kb()
    )

# ============ ЗАНЯТЬ МЕСТО ============
@dp.message(F.text == "🚀 ЗАНЯТЬ МЕСТО")
async def take_place(msg: types.Message):
    user_id = str(msg.from_user.id)
    if user_id not in users:
        await msg.answer("Нажмите /start сначала.")
        return

    # Проверяем, подписан ли пользователь на твой канал
    try:

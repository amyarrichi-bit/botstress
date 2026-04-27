import asyncio
import json
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

DATA_FILE = "data.json"

questions = [
    "1. Сегодня я чувствую себя напряжённым(ой) или перегруженным(ой).",
    "2. Мне было сложно сосредоточиться на рабочих задачах.",
    "3. Объём задач сегодня казался чрезмерным.",
    "4. Я чувствовал(а) усталость уже в середине рабочего дня.",
    "5. У меня возникали раздражение или негативные эмоции на работе.",
    "6. Мне не хватало времени, чтобы выполнить всё запланированное.",
    "7. В целом я испытываю стресс из-за работы сегодня."
]

user_data = {}

# 📦 загрузка JSON
def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

# 💾 сохранение JSON
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# 🔘 клавиатура
def get_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1", callback_data="1"),
            InlineKeyboardButton(text="2", callback_data="2"),
            InlineKeyboardButton(text="3", callback_data="3"),
            InlineKeyboardButton(text="4", callback_data="4"),
            InlineKeyboardButton(text="5", callback_data="5"),
        ]
    ])

# ▶️ старт + статистика
@dp.message()
async def start(message: types.Message):
    data = load_data()
    today = datetime.now().strftime("%Y-%m-%d")

    # /start
    if message.text == "/start":
        user_id = str(message.from_user.id)

        if today not in data:
            data[today] = {"users": {}}

        if len(data[today]["users"]) >= 10 and user_id not in data[today]["users"]:
            await message.answer("Сегодня уже 10 человек прошли тест 🙌")
            return

        user_data[user_id] = {"step": 0, "score": 0}
        await message.answer(questions[0], reply_markup=get_keyboard())

    # /stats
    elif message.text == "/stats":
        today = datetime.now().strftime("%Y-%m-%d")
        data = load_data()

        if today in data and data[today]["users"]:
            scores = list(data[today]["users"].values())
            avg = sum(scores) / len(scores)
            await message.answer(
                f"📊 Сегодня прошло: {len(scores)} / 10\n"
                f"Средний стресс: {avg:.2f}"
            )
        else:
            await message.answer("Пока нет данных за сегодня")

# 🔘 ответы
@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    user_id = str(callback.from_user.id)
    value = int(callback.data)

    if user_id not in user_data:
        await callback.answer("Нажми /start")
        return

    user_data[user_id]["score"] += value
    user_data[user_id]["step"] += 1

    step = user_data[user_id]["step"]

    if step < len(questions):
        await callback.message.edit_text(
            questions[step],
            reply_markup=get_keyboard()
        )
    else:
        total = user_data[user_id]["score"]

        if total <= 14:
            result = "Низкий уровень стресса"
        elif total <= 24:
            result = "Умеренный стресс"
        else:
            result = "Высокий стресс"

        today = datetime.now().strftime("%Y-%m-%d")
        data = load_data()

        if today not in data:
            data[today] = {"users": {}}

        # 💾 сохраняем пользователя
        data[today]["users"][user_id] = total
        save_data(data)

        await callback.message.edit_text(
            f"Результат: {total}\n{result}"
        )

        del user_data[user_id]

    await callback.answer()

# 🚀 запуск
async def main():
    await dp.start_polling(bot)

asyncio.run(main())

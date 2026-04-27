import asyncio
import json
import os
from datetime import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

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


def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        return {}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def get_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1", callback_data="score:1"),
            InlineKeyboardButton(text="2", callback_data="score:2"),
            InlineKeyboardButton(text="3", callback_data="score:3"),
            InlineKeyboardButton(text="4", callback_data="score:4"),
            InlineKeyboardButton(text="5", callback_data="score:5"),
        ]
    ])


def stats_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Посмотреть статистику", callback_data="show_stats")]
    ])


def get_today():
    return datetime.now().strftime("%Y-%m-%d")


def get_average_stats():
    data = load_data()
    today = get_today()

    if today not in data or not data[today].get("users"):
        return None, 0

    scores = list(data[today]["users"].values())
    avg = sum(scores) / len(scores)
    count = len(scores)
    return avg, count


def get_result_text(total):
    if total <= 14:
        return "Низкий уровень стресса"
    elif total <= 24:
        return "Умеренный стресс"
    else:
        return "Высокий стресс"


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = str(message.from_user.id)
    today = get_today()
    data = load_data()

    if today not in data:
        data[today] = {"users": {}}

    if len(data[today]["users"]) >= 10 and user_id not in data[today]["users"]:
        avg, count = get_average_stats()
        text = "Сегодня уже 10 человек прошли тест 🙌"
        if avg is not None:
            text += f"\n\n📊 Уже прошло: {count} / 10\nСредний стресс: {avg:.2f}"
        await message.answer(text, reply_markup=stats_keyboard())
        return

    user_data[user_id] = {"step": 0, "score": 0}

    await message.answer(
        "Пройди короткий тест по шкале 1–5.\n\n" + questions[0],
        reply_markup=get_keyboard()
    )


@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    avg, count = get_average_stats()

    if avg is None:
        await message.answer("Пока нет данных за сегодня.")
        return

    await message.answer(
        f"📊 Статистика за сегодня:\n"
        f"Прошло: {count} / 10\n"
        f"Средний уровень стресса: {avg:.2f}"
    )


@dp.callback_query(lambda c: c.data == "show_stats")
async def show_stats(callback: types.CallbackQuery):
    avg, count = get_average_stats()

    if avg is None:
        await callback.message.answer("Пока нет данных за сегодня.")
    else:
        await callback.message.answer(
            f"📊 Статистика за сегодня:\n"
            f"Прошло: {count} / 10\n"
            f"Средний уровень стресса: {avg:.2f}"
        )

    await callback.answer()


@dp.callback_query(lambda c: c.data and c.data.startswith("score:"))
async def handle_callback(callback: types.CallbackQuery):
    user_id = str(callback.from_user.id)

    if user_id not in user_data:
        await callback.answer("Нажми /start")
        return

    try:
        value = int(callback.data.split(":")[1])
    except (IndexError, ValueError):
        await callback.answer("Ошибка данных")
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
        result = get_result_text(total)

        today = get_today()
        data = load_data()

        if today not in data:
            data[today] = {"users": {}}

        data[today]["users"][user_id] = total
        save_data(data)

        avg, count = get_average_stats()

        text = (
            f"Твой результат: {total}\n"
            f"{result}\n\n"
            f"📊 Сегодня прошло: {count} / 10"
        )

        if avg is not None:
            text += f"\nСредний стресс по офису: {avg:.2f}"

        await callback.message.edit_text(text, reply_markup=stats_keyboard())

        del user_data[user_id]

    await callback.answer()


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8584246495:AAFXctUB0uK4ymTK1U_fGm3v6LjK0X6PcL4"

bot = Bot(token=TOKEN)
dp = Dispatcher()

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

# 🔘 Кнопки 1–5
def get_keyboard():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1", callback_data="1"),
            InlineKeyboardButton(text="2", callback_data="2"),
            InlineKeyboardButton(text="3", callback_data="3"),
            InlineKeyboardButton(text="4", callback_data="4"),
            InlineKeyboardButton(text="5", callback_data="5"),
        ]
    ])
    return kb

# ▶️ старт
@dp.message()
async def start(message: types.Message):
    if message.text == "/start":
        user_id = message.from_user.id
        user_data[user_id] = {"step": 0, "score": 0}
        await message.answer(
            "Оцени по шкале 1–5:\n\n" + questions[0],
            reply_markup=get_keyboard()
        )

    elif message.text == "/stats":
        try:
            scores = []
            with open("results.txt", "r") as f:
                for line in f:
                    scores.append(int(line.strip()))

            if scores:
                avg = sum(scores) / len(scores)
                await message.answer(f"📊 Средний уровень стресса: {avg:.2f}")
            else:
                await message.answer("Пока нет данных")
        except:
            await message.answer("Пока нет данных")

# 🔘 обработка кнопок
@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    if user_id not in user_data:
        await callback.answer("Нажми /start")
        return

    value = int(callback.data)
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
            result = "Высокий уровень стресса"

        await callback.message.edit_text(
            f"Твой результат: {total}\n{result}"
        )

        # 💾 сохраняем только балл
        with open("results.txt", "a") as f:
            f.write(f"{total}\n")

        del user_data[user_id]

    await callback.answer()

# 🚀 запуск
async def main():
    await dp.start_polling(bot)

asyncio.run(main())

import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import os

API_TOKEN = "7999512901:AAGg3X5JRAWzDm9GqkvnVR7ur14HVsKYYrc"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Состояния для FSM
class CalcStates(StatesGroup):
    waiting_for_length = State()
    waiting_for_density = State()
    waiting_for_confirm = State()
    waiting_for_quiz = State()

# Клавиатуры
def main_menu():
    kb = ReplyKeyboardBuilder()
    kb.add(KeyboardButton("🔢 Сделать расчёт"))
    kb.add(KeyboardButton("💾 Мои расчёты"))
    kb.add(KeyboardButton("💡 Советы и лайфхаки"))
    kb.add(KeyboardButton("📦 Материалы"))
    kb.add(KeyboardButton("📝 Квиз"))
    kb.add(KeyboardButton("🔁 Новый расчёт"))
    return kb.as_markup(resize_keyboard=True)

# Цены по плотности (руб/м2)
PRICE_BY_DENSITY = {
    100: 50,
    150: 55,
    200: 60,
    250: 65,
    300: 70,
}

FIXED_WIDTH = 2  # ширина рулона, метры

# Стартовый обработчик
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        f"Привет, {message.from_user.first_name}! Это бот-калькулятор геотекстиля.\n"
        f"Ширина всех рулонов — фиксированная: {FIXED_WIDTH} м.\n"
        f"Выбери действие в меню ниже.",
        reply_markup=main_menu()
    )

# Обработка нажатия на кнопку "🔢 Сделать расчёт"
@dp.message(lambda m: m.text == "🔢 Сделать расчёт")
async def start_calc(message: types.Message, state: FSMContext):
    await message.answer("Введите длину участка в метрах:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(CalcStates.waiting_for_length)

# Получение длины
@dp.message(CalcStates.waiting_for_length)
async def process_length(message: types.Message, state: FSMContext):
    try:
        length = float(message.text.replace(',', '.'))
        if length <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число длины участка в метрах.")
        return

    await state.update_data(length=length)
    kb = ReplyKeyboardBuilder()
    for density in PRICE_BY_DENSITY.keys():
        kb.add(KeyboardButton(str(density)))
    await message.answer("Выберите плотность геотекстиля (г/м²):", reply_markup=kb.as_markup(resize_keyboard=True))
    await state.set_state(CalcStates.waiting_for_density)

# Получение плотности
@dp.message(CalcStates.waiting_for_density)
async def process_density(message: types.Message, state: FSMContext):
    try:
        density = int(message.text)
        if density not in PRICE_BY_DENSITY:
            raise ValueError
    except ValueError:
        await message.answer("Пожалуйста, выберите плотность из списка кнопок.")
        return

    data = await state.get_data()
    length = data['length']

    # Добавляем запас 20%, если площадь < 100 м²
    area = FIXED_WIDTH * length
    if area < 100:
        area *= 1.2

    price_per_m2 = PRICE_BY_DENSITY[density]
    total_price = round(area * price_per_m2, 2)
    total_area = round(area, 2)

    result_text = (
        f"Расчёт:\n"
        f"Ширина рулона: {FIXED_WIDTH} м\n"
        f"Длина участка: {length} м\n"
        f"Площадь (с запасом при необходимости): {total_area} м²\n"
        f"Плотность: {density} г/м²\n"
        f"Цена за м²: {price_per_m2} руб.\n"
        f"Итого: {total_price} руб."
    )

    await message.answer(result_text, reply_markup=main_menu())
    await state.clear()

# Обработка остальных кнопок меню (пример)
@dp.message(lambda m: m.text == "💾 Мои расчёты")
async def my_calculations(message: types.Message):
    await message.answer("Здесь будет ваша история расчётов.", reply_markup=main_menu())

@dp.message(lambda m: m.text == "💡 Советы и лайфхаки")
async def tips_and_tricks(message: types.Message):
    await message.answer("Советы по применению геотекстиля:\n- ...\n- ...", reply_markup=main_menu())

@dp.message(lambda m: m.text == "📦 Материалы")
async def materials(message: types.Message):
    await message.answer(
        "Доступные материалы:\n"
        "- Геотекстиль (разные плотности)\n"
        "- Геосетка\n"
        "- Биомат\n"
        "- Спанбонд\n"
        "- Георешётка\n",
        reply_markup=main_menu()
    )

@dp.message(lambda m: m.text == "📝 Квиз")
async def quiz_start(message: types.Message, state: FSMContext):
    await message.answer(
        "Зачем нужен геотекстиль?\n"
        "Выберите вариант:\n"
        "1. Парковка\n"
        "2. Отмостка\n"
        "3. Дренаж\n"
        "4. Дорожка\n"
        "Отправьте номер варианта.",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(CalcStates.waiting_for_quiz)

@dp.message(CalcStates.waiting_for_quiz)
async def quiz_answer(message: types.Message, state: FSMContext):
    answers = {
        "1": "Рекомендуется плотность 250 г/м² для парковки.",
        "2": "Рекомендуется плотность 150 г/м² для отмостки.",
        "3": "Рекомендуется плотность 200 г/м² для дренажа.",
        "4": "Рекомендуется плотность 100 г/м² для дорожки."
    }
    text = answers.get(message.text)
    if text is None:
        await message.answer("Пожалуйста, выберите вариант из списка, отправив номер.")
        return
    await message.answer(text, reply_markup=main_menu())
    await state.clear()

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))

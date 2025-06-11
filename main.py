from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, StateFilter
from aiogram.filters.text import TextFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.bot import DefaultBotProperties

import logging
import os

API_TOKEN = "7999512901:AAGg3X5JRAWzDm9GqkvnVR7ur14HVsKYYrc"

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="HTML"), session=AiohttpSession())
dp = Dispatcher()

# Состояния
class CalcStates(StatesGroup):
    waiting_for_length = State()
    waiting_for_density = State()
    quiz = State()

# Фиксированные цены и плотности
DENSITIES = {
    "100": 50,
    "150": 55,
    "200": 60,
    "250": 65,
    "300": 70,
}

WIDTH_M = 2  # ширина всегда 2 метра

# Главное меню
def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(
        KeyboardButton("🔢 Сделать расчёт"),
        KeyboardButton("💾 Мои расчёты")
    )
    kb.add(
        KeyboardButton("💡 Советы и лайфхаки"),
        KeyboardButton("📦 Материалы")
    )
    kb.add(
        KeyboardButton("📝 Квиз"),
        KeyboardButton("🔁 Новый расчёт")
    )
    return kb

# Старт
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"Привет, {message.from_user.first_name}! 🛠\n"
        "Я помогу рассчитать количество и стоимость геотекстиля.\n\n"
        "Выбери действие в меню ниже.",
        reply_markup=main_menu()
    )

# Начало расчёта (старт или новый расчёт)
@dp.message(TextFilter(text=["🔢 Сделать расчёт", "🔁 Новый расчёт"]))
async def start_calc(message: types.Message, state: FSMContext):
    await state.set_state(CalcStates.waiting_for_length)
    await message.answer(
        "Введите длину участка в метрах (ширина фиксирована 2 метра):",
        reply_markup=ReplyKeyboardRemove()
    )

# Обработка длины участка
@dp.message(StateFilter(CalcStates.waiting_for_length))
async def process_length(message: types.Message, state: FSMContext):
    try:
        length = float(message.text.replace(",", "."))
        if length <= 0:
            raise ValueError()
    except ValueError:
        await message.answer("Пожалуйста, введите корректное положительное число длины участка в метрах.")
        return

    # Сохраняем длину в состоянии
    await state.update_data(length=length)

    # Предлагаем выбрать плотность
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for density in DENSITIES.keys():
        kb.add(KeyboardButton(density))

    await state.set_state(CalcStates.waiting_for_density)
    await message.answer(
        "Выберите плотность геотекстиля (г/м²):",
        reply_markup=kb
    )

# Обработка выбора плотности и расчет
@dp.message(StateFilter(CalcStates.waiting_for_density))
async def process_density(message: types.Message, state: FSMContext):
    density = message.text.strip()
    if density not in DENSITIES:
        await message.answer("Пожалуйста, выберите плотность из предложенного списка.")
        return

    data = await state.get_data()
    length = data.get("length")
    if not length:
        await message.answer("Произошла ошибка, попробуйте начать расчет заново.")
        await state.clear()
        return

    price_per_m2 = DENSITIES[density]

    # Расчет площади с запасом +20% если меньше 100 м²
    area = WIDTH_M * length
    if area < 100:
        area *= 1.2  # +20% запас

    area = round(area, 2)
    total_price = round(area * price_per_m2, 2)

    result = (
        f"Расчёт для участка {length} м × {WIDTH_M} м\n"
        f"Площадь с запасом: {area} м²\n"
        f"Плотность: {density} г/м²\n"
        f"Цена за м²: {price_per_m2} ₽\n\n"
        f"<b>Итоговая стоимость:</b> {total_price} ₽"
    )

    # Сохраняем расчёт в состоянии (можно расширить для сохранения в базу)
    user_data = await state.get_data()
    calc_history = user_data.get("calc_history", [])
    calc_history.append(result)
    await state.update_data(calc_history=calc_history)

    await message.answer(result, reply_markup=main_menu())
    await state.clear()

# Показать мои расчёты
@dp.message(TextFilter(text="💾 Мои расчёты"))
async def show_calcs(message: types.Message, state: FSMContext):
    data = await state.get_data()
    calc_history = data.get("calc_history", [])
    if not calc_history:
        await message.answer("У вас пока нет сохранённых расчётов.", reply_markup=main_menu())
        return

    text = "<b>Ваши расчёты:</b>\n\n" + "\n\n".join(calc_history)
    await message.answer(text, reply_markup=main_menu())

# Советы и лайфхаки
@dp.message(TextFilter(text="💡 Советы и лайфхаки"))
async def tips_and_hacks(message: types.Message):
    text = (
        "<b>Советы по применению геотекстиля:</b>\n"
        "- Для дренажа используйте плотность от 150 г/м²\n"
        "- Для дорожек и парковок — от 200 г/м²\n"
        "- Добавляйте запас материала +20% при расчётах менее 100 м²\n"
        "- Учитывайте ровность поверхности при укладке\n"
        "- Материал устойчив к гниению и ультрафиолету\n"
        "..."
    )
    await message.answer(text, reply_markup=main_menu())

# Информация о материалах
@dp.message(TextFilter(text="📦 Материалы"))
async def materials_info(message: types.Message):
    text = (
        "<b>Материалы:</b>\n\n"
        "<b>Геотекстиль:</b> термоскреплённое полотно, применяется для разделения, фильтрации и дренажа.\n\n"
        "<b>Геосетка:</b> армирующий материал для укрепления грунта.\n\n"
        "<b>Биоматы:</b> используются для защиты склонов и озеленения.\n\n"
        "<b>Спанбонд:</b> нетканый материал для временной защиты растений и грунта.\n\n"
        "<b>Объемная георешетка:</b> для укрепления склонов и создания дренажных систем."
    )
    await message.answer(text, reply_markup=main_menu())

# Квиз (пример простой реализации)
QUIZ_QUESTIONS = [
    {
        "question": "Зачем нужен геотекстиль?",
        "options": [
            "Для дренажа",
            "Для укрепления грунта",
            "Для декоративного покрытия",
            "Для утепления"
        ],
        "correct": 0,  # индекс правильного ответа
        "recommend": {
            0: "Рекомендуется плотность 150 г/м²",
            1: "Рекомендуется плотность 200 г/м²",
            2: "Геотекстиль не подходит для декоративных целей",
            3: "Геотекстиль не используется как утеплитель"
        }
    }
]

@dp.message(TextFilter(text="📝 Квиз"))
async def start_quiz(message: types.Message, state: FSMContext):
    await state.update_data(quiz_step=0)
    question = QUIZ_QUESTIONS[0]["question"]
    options = QUIZ_QUESTIONS[0]["options"]
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for opt in options:
        kb.add(KeyboardButton(opt))
    await state.set_state(CalcStates.quiz)
    await message.answer(f"<b>Вопрос:</b> {question}", reply_markup=kb)

@dp.message(StateFilter(CalcStates.quiz))
async def quiz_answer(message: types.Message, state: FSMContext):
    data = await state.get_data()
    step = data.get("quiz_step", 0)
    user_answer = message.text.strip()
    question_data = QUIZ_QUESTIONS[step]

    if user_answer not in question_data["options"]:
        await message.answer("Пожалуйста, выберите вариант из списка.")
        return

    idx = question_data["options"].index(user_answer)
    recommendation = question_data["recommend"].get(idx, "Нет рекомендации для этого варианта.")

    await message.answer(f"Рекомендация: {recommendation}", reply_markup=main_menu())
    await state.clear()

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, Text, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.client.session import DefaultBotProperties
from aiogram.enums import ParseMode
import asyncio

API_TOKEN = "7999512901:AAGg3X5JRAWzDm9GqkvnVR7ur14HVsKYYrc"

bot = Bot(
    token=API_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

WIDTH = 2
PRICE_BY_DENSITY = {
    100: 50,
    150: 55,
    200: 60,
    250: 65,
    300: 70,
}

class CalcStates(StatesGroup):
    waiting_for_length = State()
    waiting_for_density = State()
    quiz = State()

def main_menu():
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton("🔢 Сделать расчёт"), KeyboardButton("💾 Мои расчёты")],
            [KeyboardButton("💡 Советы и лайфхаки"), KeyboardButton("📦 Материалы")],
            [KeyboardButton("📝 Квиз"), KeyboardButton("🔁 Новый расчёт")],
        ],
        resize_keyboard=True
    )
    return kb

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"Привет, {message.from_user.first_name}! Выберите действие:",
        reply_markup=main_menu()
    )

@dp.message(Text(equals=["🔢 Сделать расчёт", "🔁 Новый расчёт"]))
async def start_calc(message: types.Message, state: FSMContext):
    await state.set_state(CalcStates.waiting_for_length)
    await message.answer(
        "Введите длину участка (в метрах). Ширина фиксирована — 2 метра.",
        reply_markup=ReplyKeyboardRemove()
    )

@dp.message(StateFilter(CalcStates.waiting_for_length))
async def process_length(message: types.Message, state: FSMContext):
    try:
        length = float(message.text.replace(",", "."))
        if length <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Введите корректное положительное число для длины.")
        return
    await state.update_data(length=length)
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for density in PRICE_BY_DENSITY.keys():
        kb.add(KeyboardButton(str(density)))
    await state.set_state(CalcStates.waiting_for_density)
    await message.answer("Выберите плотность геотекстиля (г/м²):", reply_markup=kb)

@dp.message(StateFilter(CalcStates.waiting_for_density))
async def process_density(message: types.Message, state: FSMContext):
    try:
        density = int(message.text)
        if density not in PRICE_BY_DENSITY:
            raise ValueError
    except ValueError:
        await message.answer("Выберите плотность из предложенных кнопок.")
        return
    data = await state.get_data()
    length = data.get("length")
    if length is None:
        await message.answer("Ошибка. Начните расчёт заново /start")
        return
    area = WIDTH * length
    if area < 100:
        area *= 1.2  # +20% запас
    price_per_m2 = PRICE_BY_DENSITY[density]
    total_cost = area * price_per_m2
    calc_result = {
        "length": length,
        "width": WIDTH,
        "density": density,
        "area": round(area, 2),
        "price_per_m2": price_per_m2,
        "total_cost": round(total_cost, 2),
    }
    await state.update_data(last_calc=calc_result)
    await message.answer(
        f"<b>Результат расчёта:</b>\n"
        f"Длина: {length} м\n"
        f"Ширина: {WIDTH} м\n"
        f"Площадь с запасом: {calc_result['area']} м²\n"
        f"Плотность: {density} г/м²\n"
        f"Цена за м²: {price_per_m2} ₽\n"
        f"Итоговая стоимость: {calc_result['total_cost']} ₽",
        reply_markup=main_menu()
    )
    await state.clear()

@dp.message(Text(equals="💾 Мои расчёты"))
async def show_calcs(message: types.Message, state: FSMContext):
    data = await state.get_data()
    last_calc = data.get("last_calc")
    if not last_calc:
        await message.answer("Пока нет сохранённых расчётов.", reply_markup=main_menu())
        return
    await message.answer(
        f"<b>Последний расчёт:</b>\n"
        f"Длина: {last_calc['length']} м\n"
        f"Ширина: {last_calc['width']} м\n"
        f"Плотность: {last_calc['density']} г/м²\n"
        f"Площадь с запасом: {last_calc['area']} м²\n"
        f"Цена за м²: {last_calc['price_per_m2']} ₽\n"
        f"Стоимость: {last_calc['total_cost']} ₽",
        reply_markup=main_menu()
    )

@dp.message(Text(equals="💡 Советы и лайфхаки"))
async def tips_and_hacks(message: types.Message):
    tips = (
        "💡 Советы по геотекстилю:\n"
        "• Добавляйте 20% запаса площади.\n"
        "• Для садовых дорожек — плотность 150 г/м².\n"
        "• Для парковок — 250-300 г/м².\n"
        "• Заказывайте через бота — бесплатная доставка по Нижнему Новгороду!\n"
        "• Храните материал в сухом месте."
    )
    await message.answer(tips, reply_markup=main_menu())

@dp.message(Text(equals="📦 Материалы"))
async def materials_info(message: types.Message):
    text = (
        "<b>Материалы:</b>\n"
        "• <b>Геотекстиль</b> — разделение, фильтрация, укрепление почвы.\n"
        "• <b>Геосетка</b> — армирование грунта и покрытий.\n"
        "• <b>Биоматы</b> — защита от эрозии почвы.\n"
        "• <b>Спанбонд</b> — укрывной материал для растений.\n"
        "• <b>Георешетка</b> — создание прочных оснований для дорог и парковок."
    )
    await message.answer(text, reply_markup=main_menu())

quiz_questions = [
    {
        "question": "Зачем нужен геотекстиль?",
        "options": [
            "Парковка",
            "Отмостка",
            "Дренаж",
            "Садовая дорожка",
            "Огород"
        ],
        "recommendations": {
            "Парковка": 300,
            "Отмостка": 200,
            "Дренаж": 150,
            "Садовая дорожка": 150,
            "Огород": 100,
        }
    }
]

@dp.message(Text(equals="📝 Квиз"))
async def start_quiz(message: types.Message, state: FSMContext):
    await state.set_state(CalcStates.quiz)
    question = quiz_questions[0]["question"]
    options = quiz_questions[0]["options"]
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    for option in options:
        kb.add(KeyboardButton(option))
    await message.answer(question, reply_markup=kb)

@dp.message(StateFilter(CalcStates.quiz))
async def quiz_answer(message: types.Message, state: FSMContext):
    answer = message.text
    recs = quiz_questions[0]["recommendations"]
    if answer not in recs:
        await message.answer("Пожалуйста, выберите вариант кнопками.")
        return
    recommended_density = recs[answer]
    await message.answer(
        f"Рекомендуемая плотность для '{answer}': {recommended_density} г/м².",
        reply_markup=main_menu()
    )
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

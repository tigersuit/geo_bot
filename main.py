import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.storage.memory import MemoryStorage
import os

API_TOKEN = os.getenv("API_TOKEN")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Фиксированная ширина рулона
FIXED_WIDTH = 2  # метра

# Цены по плотности (рублей за м²)
PRICE_BY_DENSITY = {
    100: 50,
    150: 55,
    200: 60,
    250: 65,
    300: 70
}

# Состояния для расчёта
class CalcStates(StatesGroup):
    waiting_for_length = State()
    waiting_for_density = State()

# Клавиатуры
main_menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔢 Сделать расчёт"), KeyboardButton(text="💾 Мои расчёты")],
        [KeyboardButton(text="💡 Советы и лайфхаки"), KeyboardButton(text="📦 Материалы")],
        [KeyboardButton(text="❓ Квиз"), KeyboardButton(text="🔁 Новый расчёт")]
    ],
    resize_keyboard=True
)

density_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="100"), KeyboardButton(text="150")],
        [KeyboardButton(text="200"), KeyboardButton(text="250")],
        [KeyboardButton(text="300"), KeyboardButton(text="Отмена")]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

# Хранилище расчётов по пользователям
user_calculations = {}

# Советы и лайфхаки
tips_text = (
    "💡 Советы и лайфхаки по работе с геотекстилем:\n"
    "- Всегда берите запас минимум 20%.\n"
    "- Укладывайте геотекстиль с нахлестом 15-20 см.\n"
    "- Используйте правильную плотность для вашего применения.\n"
    "- Заказывайте доставку через бота и получите бонус!\n"
)

# Справочник материалов
materials_text = (
    "📦 Справочник материалов:\n"
    "• Геотекстиль — предотвращает смешивание слоев грунта и улучшает дренаж.\n"
    "• Спанбонд — лёгкий нетканый материал для укрытий и защиты.\n"
    "• Геосетка — армирующий элемент для укрепления грунтов.\n"
    "• Георешётка — для стабилизации склонов и дорожных оснований.\n"
)

# Квиз вопросы и рекомендации по плотности
quiz_questions = [
    ("Выберите цель использования геотекстиля:", [
        ("Парковка", 300),
        ("Отмостка вокруг дома", 200),
        ("Дренаж", 150),
        ("Садовые дорожки", 100),
        ("Укрепление склонов", 250)
    ])
]

# --- Хендлеры ---

@dp.message(commands=["start"])
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"Привет, {message.from_user.first_name}! Я помогу рассчитать нужное количество геотекстиля.\n\n"
        "Выбери действие из меню ниже.",
        reply_markup=main_menu_kb
    )

@dp.message(F.text == "🔢 Сделать расчёт")
async def start_calculation(message: types.Message, state: FSMContext):
    await state.set_state(CalcStates.waiting_for_length)
    await message.answer(
        "Введите длину участка в метрах (ширина всегда 2 метра):",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Отмена")]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )

@dp.message(CalcStates.waiting_for_length)
async def process_length(message: types.Message, state: FSMContext):
    if message.text.lower() == "отмена":
        await state.clear()
        await message.answer("Расчёт отменён.", reply_markup=main_menu_kb)
        return

    try:
        length = float(message.text.replace(",", "."))
        if length <= 0:
            raise ValueError()
    except ValueError:
        await message.answer("Пожалуйста, введите корректное положительное число для длины.")
        return

    await state.update_data(length=length)
    await state.set_state(CalcStates.waiting_for_density)
    await message.answer("Выберите плотность геотекстиля (г/м²):", reply_markup=density_kb)

@dp.message(CalcStates.waiting_for_density)
async def process_density(message: types.Message, state: FSMContext):
    if message.text.lower() == "отмена":
        await state.clear()
        await message.answer("Расчёт отменён.", reply_markup=main_menu_kb)
        return

    try:
        density = int(message.text)
        if density not in PRICE_BY_DENSITY:
            raise ValueError()
    except ValueError:
        await message.answer("Пожалуйста, выберите плотность из предложенных вариантов.")
        return

    data = await state.get_data()
    length = data.get("length")
    width = FIXED_WIDTH
    area = length * width
    # Запас 20% при площади < 100
    if area < 100:
        area *= 1.2

    price_per_m2 = PRICE_BY_DENSITY[density]
    total_price = round(area * price_per_m2, 2)

    result_text = (
        f"Расчёт геотекстиля:\n"
        f"Длина: {length} м\n"
        f"Ширина: {width} м (фиксированная)\n"
        f"Площадь: {area:.2f} м² (с запасом)\n"
        f"Плотность: {density} г/м²\n"
        f"Цена за м²: {price_per_m2} ₽\n"
        f"Итоговая стоимость: {total_price} ₽\n\n"
        "Спасибо за заказ через бота! Доставка по Нижнему Новгороду бесплатно при заказе здесь."
    )

    # Сохраняем расчёт
    user_id = message.from_user.id
    if user_id not in user_calculations:
        user_calculations[user_id] = []
    user_calculations[user_id].append({
        "length": length,
        "width": width,
        "area": round(area, 2),
        "density": density,
        "price_per_m2": price_per_m2,
        "total_price": total_price
    })

    await message.answer(result_text, reply_markup=main_menu_kb)
    await state.clear()

@dp.message(F.text == "💾 Мои расчёты")
async def show_calculations(message: types.Message):
    user_id = message.from_user.id
    calcs = user_calculations.get(user_id)
    if not calcs:
        await message.answer("У вас ещё нет сохранённых расчётов.", reply_markup=main_menu_kb)
        return

    response = "💾 Ваши сохранённые расчёты:\n\n"
    for i, calc in enumerate(calcs, 1):
        response += (
            f"{i}. Длина: {calc['length']} м, "
            f"Площадь: {calc['area']} м², "
            f"Плотность: {calc['density']} г/м², "
            f"Цена: {calc['total_price']} ₽\n"
        )
    await message.answer(response, reply_markup=main_menu_kb)

@dp.message(F.text == "💡 Советы и лайфхаки")
async def send_tips(message: types.Message):
    await message.answer(tips_text, reply_markup=main_menu_kb)

@dp.message(F.text == "📦 Материалы")
async def send_materials(message: types.Message):
    await message.answer(materials_text, reply_markup=main_menu_kb)

# Квиз
class QuizStates(StatesGroup):
    waiting_for_answer = State()

@dp.message(F.text == "❓ Квиз")
async def start_quiz(message: types.Message, state: FSMContext):
    question, answers = quiz_questions[0]
    keyboard = InlineKeyboardMarkup(row_width=1)
    for answer_text, density in answers:
        keyboard.add(InlineKeyboardButton(text=answer_text, callback_data=f"quiz_{density}"))
    await state.set_state(QuizStates.waiting_for_answer)
    await message.answer(question, reply_markup=keyboard)

@dp.callback_query(lambda c: c.data and c.data.startswith("quiz_"))
async def process_quiz_answer(callback: types.CallbackQuery, state: FSMContext):
    density = int(callback.data.split("_")[1])
    await callback.message.answer(
        f"Рекомендуемая плотность геотекстиля для вашего применения: {density} г/м²"
    )
    await state.clear()
    await callback.message.answer("Вернуться в главное меню:", reply_markup=main_menu_kb)
    await callback.answer()

@dp.message(F.text == "🔁 Новый расчёт")
async def new_calc(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Начинаем новый расчёт.", reply_markup=main_menu_kb)

@dp.message(F.text.lower() == "отмена")
async def cancel_action(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Действие отменено.", reply_markup=main_menu_kb)

@dp.message()
async def fallback(message: types.Message):
    await message.answer("Пожалуйста, выберите действие из меню ниже.", reply_markup=main_menu_kb)

if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))

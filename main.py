import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, StateFilter, Text
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.client.bot import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession

API_TOKEN = "7999512901:AAGg3X5JRAWzDm9GqkvnVR7ur14HVsKYYrc"

logging.basicConfig(level=logging.INFO)

# Цены за м2 по плотности
PRICES = {
    100: 50,
    150: 55,
    200: 60,
    250: 65,
    300: 70,
}

WIDTH = 2  # фиксированная ширина

# FSM состояния
class CalcStates(StatesGroup):
    waiting_for_length = State()
    waiting_for_density = State()
    waiting_for_quiz_answer = State()

# Главное меню клавиатура
def main_menu_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(
        KeyboardButton("🔢 Сделать расчёт"),
        KeyboardButton("💾 Мои расчёты"),
    )
    kb.add(
        KeyboardButton("💡 Советы и лайфхаки"),
        KeyboardButton("📦 Материалы"),
    )
    kb.add(
        KeyboardButton("🔁 Новый расчёт"),
        KeyboardButton("📝 Квиз"),
    )
    return kb

# Клавиатура выбора плотности
def density_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for density in PRICES.keys():
        kb.add(KeyboardButton(str(density)))
    return kb

# Клавиатура для квиза
QUIZ_OPTIONS = {
    "Парковка": 300,
    "Дорожка": 150,
    "Отмостка": 200,
    "Дренаж": 250,
    "Газон": 100,
}

def quiz_kb():
    kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for option in QUIZ_OPTIONS.keys():
        kb.add(KeyboardButton(option))
    return kb

# Советы и лайфхаки
ADVICES_TEXT = (
    "💡 Советы и лайфхаки по работе с геотекстилем:\n"
    "- Добавляйте запас 20% при площади меньше 100 м².\n"
    "- Используйте плотность в зависимости от назначения.\n"
    "- При укладке ровняйте поверхность и убирайте мусор.\n"
    "- Закрепляйте материал, чтобы он не смещался."
)

# Материалы
MATERIALS_TEXT = (
    "📦 Материалы:\n"
    "• Геотекстиль – прочный нетканый материал для фильтрации и разделения слоёв.\n"
    "• Геосетка – армирующая сетка для укрепления грунтов.\n"
    "• Биоматы – натуральные волокна для защиты почвы от эрозии.\n"
    "• Спанбонд – легкий укрывной материал для защиты растений.\n"
    "• Георешетка – объемная конструкция для стабилизации грунтов."
)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="HTML"), session=AiohttpSession())
dp = Dispatcher()

# Хранилище расчетов по пользователям (простейшее в памяти)
user_calculations = {}

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"Привет, {message.from_user.first_name}! Я бот-калькулятор для геотекстиля.\n"
        "Выберите действие в меню ниже.",
        reply_markup=main_menu_kb()
    )

@dp.message(Text("🔢 Сделать расчёт"))
async def start_calc(message: types.Message, state: FSMContext):
    await state.set_state(CalcStates.waiting_for_length)
    await message.answer(
        "Пожалуйста, введите длину участка в метрах (ширина всегда 2 метра):",
        reply_markup=ReplyKeyboardRemove()
    )

@dp.message(StateFilter(CalcStates.waiting_for_length))
async def process_length(message: types.Message, state: FSMContext):
    try:
        length = float(message.text.replace(",", "."))
        if length <= 0:
            raise ValueError()
    except ValueError:
        await message.answer("Пожалуйста, введите корректное положительное число длины участка в метрах.")
        return
    await state.update_data(length=length)
    await state.set_state(CalcStates.waiting_for_density)
    await message.answer("Выберите плотность геотекстиля:", reply_markup=density_kb())

@dp.message(StateFilter(CalcStates.waiting_for_density))
async def process_density(message: types.Message, state: FSMContext):
    try:
        density = int(message.text)
        if density not in PRICES:
            raise ValueError()
    except ValueError:
        await message.answer("Пожалуйста, выберите плотность из списка кнопок.")
        return
    data = await state.get_data()
    length = data.get("length")

    area = WIDTH * length
    if area < 100:
        area_with_buffer = area * 1.2
    else:
        area_with_buffer = area

    price_per_m2 = PRICES[density]
    total_cost = round(area_with_buffer * price_per_m2, 2)
    area_with_buffer = round(area_with_buffer, 2)

    # Сохраняем расчет
    user_id = message.from_user.id
    user_calculations.setdefault(user_id, [])
    user_calculations[user_id].append({
        "length": length,
        "width": WIDTH,
        "density": density,
        "area": area_with_buffer,
        "price_per_m2": price_per_m2,
        "total_cost": total_cost
    })

    await message.answer(
        f"Результат расчёта:\n"
        f"Длина: {length} м\n"
        f"Ширина: {WIDTH} м (фиксированная)\n"
        f"Площадь с запасом: {area_with_buffer} м²\n"
        f"Плотность: {density} г/м²\n"
        f"Цена за м²: {price_per_m2} ₽\n"
        f"Итоговая стоимость: {total_cost} ₽",
        reply_markup=main_menu_kb()
    )
    await state.clear()

@dp.message(Text("💾 Мои расчёты"))
async def show_calculations(message: types.Message):
    user_id = message.from_user.id
    calcs = user_calculations.get(user_id)
    if not calcs:
        await message.answer("У вас пока нет сохранённых расчётов.", reply_markup=main_menu_kb())
        return
    text = "Ваши расчёты:\n\n"
    for i, calc in enumerate(calcs, 1):
        text += (
            f"{i}. Длина: {calc['length']} м, "
            f"Ширина: {calc['width']} м, "
            f"Плотность: {calc['density']} г/м², "
            f"Площадь с запасом: {calc['area']} м², "
            f"Цена за м²: {calc['price_per_m2']} ₽, "
            f"Итоговая стоимость: {calc['total_cost']} ₽\n"
        )
    await message.answer(text, reply_markup=main_menu_kb())

@dp.message(Text("💡 Советы и лайфхаки"))
async def show_advices(message: types.Message):
    await message.answer(ADVICES_TEXT, reply_markup=main_menu_kb())

@dp.message(Text("📦 Материалы"))
async def show_materials(message: types.Message):
    await message.answer(MATERIALS_TEXT, reply_markup=main_menu_kb())

@dp.message(Text("🔁 Новый расчёт"))
async def new_calc(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Начинаем новый расчёт. Введите длину участка в метрах:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(CalcStates.waiting_for_length)

# Квиз

@dp.message(Text("📝 Квиз"))
async def start_quiz(message: types.Message, state: FSMContext):
    await state.set_state(CalcStates.waiting_for_quiz_answer)
    await message.answer("Для чего вам нужен геотекстиль? Выберите вариант:", reply_markup=quiz_kb())

@dp.message(StateFilter(CalcStates.waiting_for_quiz_answer))
async def process_quiz_answer(message: types.Message, state: FSMContext):
    choice = message.text
    density = QUIZ_OPTIONS.get(choice)
    if density is None:
        await message.answer("Пожалуйста, выберите вариант из кнопок.")
        return
    await message.answer(
        f"Для {choice.lower()} рекомендуем плотность: {density} г/м².",
        reply_markup=main_menu_kb()
    )
    await state.clear()

# Обработка неизвестных сообщений
@dp.message()
async def unknown_message(message: types.Message):
    await message.answer("Пожалуйста, используйте меню ниже для взаимодействия с ботом.", reply_markup=main_menu_kb())

# Запуск бота
if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))

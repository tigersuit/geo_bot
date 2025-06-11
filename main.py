import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.enums.parse_mode import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import ReplyKeyboardRemove
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import types

API_TOKEN = "7999512901:AAGg3X5JRAWzDm9GqkvnVR7ur14HVsKYYrc"

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
logging.basicConfig(level=logging.INFO)

# --- FSM States ---
class CalcState(StatesGroup):
    waiting_for_length = State()
    waiting_for_density = State()

user_data = {}

# --- Кнопки ---
main_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="🔢 Сделать расчёт"), KeyboardButton(text="💾 Мои расчёты")],
    [KeyboardButton(text="💡 Советы и лайфхаки"), KeyboardButton(text="📦 Материалы")],
    [KeyboardButton(text="📝 Квиз"), KeyboardButton(text="🔁 Новый расчёт")]
], resize_keyboard=True)

# --- Цены по плотности ---
density_prices = {
    100: 50,
    150: 55,
    200: 60,
    250: 65,
    300: 70
}

# --- Старт ---
@dp.message(F.text == "/start")
async def start(message: Message, state: FSMContext):
    await message.answer(f"Привет, {message.from_user.first_name}! 👋\nВыбери действие:", reply_markup=main_kb)

# --- Обработка кнопок ---
@dp.message()
async def handle_menu(message: Message, state: FSMContext):
    text = message.text

    if text == "🔢 Сделать расчёт" or text == "🔁 Новый расчёт":
        await message.answer("Введите длину участка в метрах:")
        await state.set_state(CalcState.waiting_for_length)

    elif text == "💾 Мои расчёты":
        data = user_data.get(message.from_user.id, [])
        if not data:
            await message.answer("У вас пока нет сохранённых расчётов.")
        else:
            history = "\n\n".join(data)
            await message.answer(f"<b>Ваши расчёты:</b>\n\n{history}")

    elif text == "💡 Советы и лайфхаки":
        await message.answer("✅ Советы по применению геотекстиля:\n\n"
                             "- Используйте плотность 150-200 г/м² для дорожек и парковок\n"
                             "- Укладывайте на утрамбованное основание\n"
                             "- Делайте нахлёст 10-20 см между полотнами")

    elif text == "📦 Материалы":
        await message.answer("📦 Основные материалы:\n\n"
                             "▪️ Геотекстиль — разделение, фильтрация, армирование\n"
                             "▪️ Геосетка — усиление основания\n"
                             "▪️ Георешетка — стабилизация склонов и дорог\n"
                             "▪️ Спанбонд — укрывной материал\n"
                             "▪️ Биоматы — защита от эрозии")

    elif text == "📝 Квиз":
        await message.answer("📝 Для чего вы хотите использовать геотекстиль?\n"
                             "1. Дорожка или отмостка — 150 г/м²\n"
                             "2. Парковка — 200 г/м²\n"
                             "3. Дренаж — 100 г/м²\n"
                             "4. Фундамент — 250-300 г/м²")

    else:
        await message.answer("Не понимаю команду. Пожалуйста, выбери пункт меню.")

# --- Обработка длины ---
@dp.message(CalcState.waiting_for_length)
async def process_length(message: Message, state: FSMContext):
    try:
        length = float(message.text.replace(",", "."))
        await state.update_data(length=length)

        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=str(d))] for d in density_prices.keys()],
            resize_keyboard=True
        )
        await message.answer("Выберите плотность геотекстиля:", reply_markup=kb)
        await state.set_state(CalcState.waiting_for_density)

    except ValueError:
        await message.answer("Введите корректное число длины в метрах.")

# --- Обработка плотности и расчёт ---
@dp.message(CalcState.waiting_for_density)
async def process_density(message: Message, state: FSMContext):
    try:
        density = int(message.text)
        if density not in density_prices:
            raise ValueError

        data = await state.get_data()
        length = data["length"]
        width = 2
        area = length * width

        if area < 100:
            area *= 1.2  # +20% запас

        area = round(area, 2)
        price_per_m2 = density_prices[density]
        total_cost = round(area * price_per_m2, 2)

        text = (f"<b>📐 Расчёт:</b>\n"
                f"Длина: {length} м\n"
                f"Ширина: {width} м\n"
                f"Площадь с запасом: {area} м²\n"
                f"Плотность: {density} г/м²\n"
                f"Цена за м²: {price_per_m2} ₽\n"
                f"<b>Итого: {total_cost} ₽</b>")

        await message.answer(text, reply_markup=main_kb)

        uid = message.from_user.id
        user_data.setdefault(uid, []).append(text)

        await state.clear()

    except Exception:
        await message.answer("Выберите плотность из списка.")

# --- Запуск ---
if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))

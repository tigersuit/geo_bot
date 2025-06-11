import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ParseMode
from aiogram import F

API_TOKEN = "7999512901:AAGg3X5JRAWzDm9GqkvnVR7ur14HVsKYYrc"

# Логирование
logging.basicConfig(level=logging.INFO)

# FSM состояния
class CalcState(StatesGroup):
    waiting_for_length = State()
    waiting_for_density = State()

# Цены по плотности
DENSITY_PRICES = {
    100: 50,
    150: 55,
    200: 60,
    250: 65,
    300: 70
}

# Создание бота
bot = Bot(token=API_TOKEN, default=types.DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# Главное меню
def main_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="🔢 Сделать расчёт")
    builder.button(text="💾 Мои расчёты")
    builder.button(text="💡 Советы и лайфхаки")
    builder.button(text="📦 Материалы")
    builder.button(text="📝 Квиз")
    builder.button(text="🔁 Новый расчёт")
    builder.adjust(2, 2, 2)
    return builder.as_markup(resize_keyboard=True)

@dp.message(F.text == "/start")
async def start(message: Message):
    await message.answer(f"Привет, {message.from_user.first_name}! 👋\nЯ помогу рассчитать геотекстиль (дорнит).", reply_markup=main_menu())

# Команда "Сделать расчёт"
@dp.message(F.text == "🔢 Сделать расчёт")
async def start_calc(message: Message, state: FSMContext):
    await state.set_state(CalcState.waiting_for_length)
    await message.answer("Введите длину участка в метрах:")

@dp.message(CalcState.waiting_for_length)
async def process_length(message: Message, state: FSMContext):
    try:
        length = float(message.text.replace(",", "."))
        await state.update_data(length=length)
        # Плотности
        builder = ReplyKeyboardBuilder()
        for d in DENSITY_PRICES.keys():
            builder.button(text=str(d))
        builder.adjust(3)
        await state.set_state(CalcState.waiting_for_density)
        await message.answer("Выберите плотность геотекстиля (г/м²):", reply_markup=builder.as_markup(resize_keyboard=True))
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число длины участка в метрах.")

@dp.message(CalcState.waiting_for_density)
async def process_density(message: Message, state: FSMContext):
    try:
        density = int(message.text)
        if density not in DENSITY_PRICES:
            raise ValueError
        data = await state.get_data()
        length = data['length']
        width = 2  # фиксированная
        area = length * width

        if area < 100:
            area *= 1.2
            reserve_text = "\nДобавлен запас 20% из-за площади < 100 м²."
        else:
            reserve_text = ""

        price_per_m2 = DENSITY_PRICES[density]
        total_price = round(area * price_per_m2, 2)

        await message.answer(
            f"📐 Площадь: {area:.2f} м²\n"
            f"📦 Плотность: {density} г/м²\n"
            f"💰 Цена за м²: {price_per_m2} ₽\n"
            f"🧾 Итог: {total_price} ₽"
            f"{reserve_text}",
            reply_markup=main_menu()
        )
        await state.clear()
    except ValueError:
        await message.answer("Пожалуйста, выберите плотность из списка.")

# Мои расчёты (заглушка)
@dp.message(F.text == "💾 Мои расчёты")
async def my_calcs(message: Message):
    await message.answer("История расчётов пока не сохраняется. Скоро будет!")

# Кнопка «Новый расчёт»
@dp.message(F.text == "🔁 Новый расчёт")
async def new_calc(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Начнём новый расчёт. Введите длину участка в метрах:")
    await state.set_state(CalcState.waiting_for_length)

# Советы и лайфхаки
@dp.message(F.text == "💡 Советы и лайфхаки")
async def tips(message: Message):
    await message.answer("💡 Лайфхаки по геотекстилю:\n\n"
                         "▪ Используйте плотность 200+ для парковки\n"
                         "▪ Укладывайте на утрамбованное основание\n"
                         "▪ Делайте нахлёст 10–20 см")

# Материалы
@dp.message(F.text == "📦 Материалы")
async def materials(message: Message):
    await message.answer(
        "<b>📦 Материалы:</b>\n"
        "▪ <b>Геотекстиль (дорнит):</b> для разделения и укрепления\n"
        "▪ <b>Геосетка:</b> усиление слабых оснований\n"
        "▪ <b>Биоматы:</b> защита склонов от эрозии\n"
        "▪ <b>Спанбонд:</b> для садоводов, не гниёт\n"
        "▪ <b>Георешётка:</b> объёмное армирование"
    )

# Квиз
@dp.message(F.text == "📝 Квиз")
async def quiz(message: Message):
    builder = ReplyKeyboardBuilder()
    builder.button(text="🚗 Парковка")
    builder.button(text="🏠 Отмостка")
    builder.button(text="💧 Дренаж")
    builder.button(text="👣 Дорожка")
    builder.adjust(2)
    await message.answer("Для чего вам нужен геотекстиль?", reply_markup=builder.as_markup(resize_keyboard=True))

@dp.message(F.text.in_({"🚗 Парковка", "🏠 Отмостка", "💧 Дренаж", "👣 Дорожка"}))
async def quiz_answer(message: Message):
    mapping = {
        "🚗 Парковка": 250,
        "🏠 Отмостка": 150,
        "💧 Дренаж": 100,
        "👣 Дорожка": 150
    }
    recommended = mapping.get(message.text)
    await message.answer(f"✅ Рекомендуем плотность: <b>{recommended} г/м²</b>", reply_markup=main_menu())

# Обработка непонятных команд
@dp.message()
async def handle_other(message: Message, state: FSMContext):
    current = await state.get_state()
    if current in [CalcState.waiting_for_length, CalcState.waiting_for_density]:
        return  # Не мешаем, бот ждёт число или выбор
    await message.answer("Не понимаю команду. Пожалуйста, выбери пункт меню.", reply_markup=main_menu())

# Запуск
if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))

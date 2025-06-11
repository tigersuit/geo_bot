import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
import os

API_TOKEN = "7999512901:AAGg3X5JRAWzDm9GqkvnVR7ur14HVsKYYrc" # Обязательно установите переменную окружения

bot = Bot(token=API_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

# Состояния
class CalcStates(StatesGroup):
    waiting_for_length = State()

# Хранилище расчётов
user_calculations = {}

# Главное меню
def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("🔢 Сделать расчёт"))
    kb.add(KeyboardButton("📝 Квиз"), KeyboardButton("💡 Советы и лайфхаки"))
    kb.add(KeyboardButton("📦 Материалы"), KeyboardButton("💾 Мои расчёты"))
    return kb

@dp.message()
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n"
        f"Я помогу рассчитать нужное количество и стоимость геотекстиля (дорнита) шириной 2 метра.",
        reply_markup=main_menu()
    )

# Расчёт
@dp.message(lambda m: m.text == "🔢 Сделать расчёт")
async def start_calc(message: types.Message, state: FSMContext):
    await message.answer("Введите длину участка в метрах (например, 10):")
    await state.set_state(CalcStates.waiting_for_length)

@dp.message(CalcStates.waiting_for_length)
async def process_length(message: types.Message, state: FSMContext):
    try:
        length = float(message.text.replace(",", "."))
        width = 2
        area = length * width
        if area < 100:
            area *= 1.2  # запас 20%
        area = round(area, 2)

        density_prices = {
            100: 50,
            150: 55,
            200: 60,
            250: 65,
            300: 70
        }

        results = "💰 <b>Результаты расчёта:</b>\n"
        for density, price in density_prices.items():
            total = round(area * price)
            results += f"\n🔹 Плотность {density} г/м²: {total} ₽ (по {price}₽/м²)"

        user_calculations[message.from_user.id] = area
        await message.answer(
            f"📐 Площадь с учётом ширины 2 м и запаса: {area} м²\n\n" + results,
            reply_markup=main_menu()
        )
        await state.clear()
    except ValueError:
        await message.answer("Введите корректное число длины участка в метрах.")

# Квиз
@dp.message(lambda m: m.text == "📝 Квиз")
async def quiz(message: types.Message):
    quiz_text = "🧠 <b>Зачем вам нужен геотекстиль?</b>\nВыберите вариант:"
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(*[
        KeyboardButton("🅿 Парковка / подъезд"),
        KeyboardButton("🚶 Дорожка / тропинка"),
        KeyboardButton("💧 Дренаж / водоотведение"),
        KeyboardButton("🏠 Отмостка вокруг дома"),
        KeyboardButton("↩ Назад в меню")
    ])
    await message.answer(quiz_text, reply_markup=kb)

@dp.message(lambda m: m.text in [
    "🅿 Парковка / подъезд", "🚶 Дорожка / тропинка",
    "💧 Дренаж / водоотведение", "🏠 Отмостка вокруг дома"
])
async def quiz_result(message: types.Message):
    mapping = {
        "🅿 Парковка / подъезд": 300,
        "🚶 Дорожка / тропинка": 200,
        "💧 Дренаж / водоотведение": 150,
        "🏠 Отмостка вокруг дома": 200
    }
    density = mapping[message.text]
    await message.answer(f"🔎 Рекомендуемая плотность геотекстиля: <b>{density} г/м²</b>", reply_markup=main_menu())

@dp.message(lambda m: m.text == "↩ Назад в меню")
async def back_to_menu(message: types.Message):
    await message.answer("Вы в главном меню.", reply_markup=main_menu())

# Советы и лайфхаки
@dp.message(lambda m: m.text == "💡 Советы и лайфхаки")
async def tips(message: types.Message):
    text = (
        "💡 <b>Полезные советы:</b>\n"
        "• Делайте нахлёст 10–15 см между полотнами.\n"
        "• Укладывайте на утрамбованное основание.\n"
        "• Закрепляйте геотекстиль скобами или засыпкой.\n"
        "• Для отмостки — минимум 150–200 г/м².\n"
        "• Для парковки — минимум 250–300 г/м².\n"
    )
    await message.answer(text, reply_markup=main_menu())

# Материалы
@dp.message(lambda m: m.text == "📦 Материалы")
async def materials(message: types.Message):
    text = (
        "📦 <b>Материалы:</b>\n"
        "• Геотекстиль (дорнит) — для разделения слоёв и дренажа.\n"
        "• Спанбонд — укрывной материал, нетканый, лёгкий.\n"
        "• Геосетка — армирует грунт, усиливает покрытие.\n"
        "• Георешётка — объёмная ячеистая конструкция.\n"
        "• Биоматы — для укрепления склонов и берегов."
    )
    await message.answer(text, reply_markup=main_menu())

# Мои расчёты
@dp.message(lambda m: m.text == "💾 Мои расчёты")
async def my_calcs(message: types.Message):
    area = user_calculations.get(message.from_user.id)
    if area:
        await message.answer(f"📌 Последний расчёт: {area} м²", reply_markup=main_menu())
    else:
        await message.answer("Вы пока не делали расчётов.", reply_markup=main_menu())

# Запуск
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

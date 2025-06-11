from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, Text
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import logging
import os

from config import API_TOKEN, CALC_FILE
from utils import save_calculation, load_calculations, ADVICES

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

class CalcStates(StatesGroup):
    waiting_for_length = State()
    waiting_for_width = State()
    waiting_for_density = State()
    waiting_for_price = State()

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔢 Сделать расчёт")],
        [KeyboardButton(text="💾 Мои расчёты")],
        [KeyboardButton(text="💡 Советы и лайфхаки")],
        [KeyboardButton(text="📦 Материалы")],
    ],
    resize_keyboard=True,
)

cancel_back_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⬅️ Назад"), KeyboardButton(text="❌ Отмена")]
    ],
    resize_keyboard=True,
)

densities = {
    "100": "Легкий (для дренажа, дорожек) — 100 г/м²",
    "150": "Средний (для парковок, отмосток) — 150 г/м²",
    "200": "Тяжелый (для усиления грунта) — 200 г/м²",
    "250": "Очень тяжелый (для промышленности) — 250 г/м²",
    "300": "Максимальный (для самых тяжелых нагрузок) — 300 г/м²"
}

# Старт и главное меню
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(f"Привет, {message.from_user.first_name}! Выберите действие:", reply_markup=main_kb)

# --- Калькулятор ---
@dp.message(Text(text="🔢 Сделать расчёт"))
async def start_calc(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Введите длину участка в метрах (например, 10.5):", reply_markup=cancel_back_kb)
    await state.set_state(CalcStates.waiting_for_length)

@dp.message(CalcStates.waiting_for_length)
async def process_length(message: types.Message, state: FSMContext):
    text = message.text
    if text == "⬅️ Назад":
        await message.answer("Возвращаемся в главное меню.", reply_markup=main_kb)
        await state.clear()
        return
    if text == "❌ Отмена":
        await message.answer("Расчёт отменён.", reply_markup=main_kb)
        await state.clear()
        return

    try:
        length = float(text.replace(",", "."))
        if length <= 0:
            raise ValueError()
        await state.update_data(length=length)
        await message.answer("Введите ширину участка в метрах (например, 5):", reply_markup=cancel_back_kb)
        await state.set_state(CalcStates.waiting_for_width)
    except ValueError:
        await message.answer("Ошибка: длина должна быть положительным числом. Попробуйте ещё раз.", reply_markup=cancel_back_kb)

@dp.message(CalcStates.waiting_for_width)
async def process_width(message: types.Message, state: FSMContext):
    text = message.text
    if text == "⬅️ Назад":
        await message.answer("Введите длину участка в метрах (например, 10.5):", reply_markup=cancel_back_kb)
        await state.set_state(CalcStates.waiting_for_length)
        return
    if text == "❌ Отмена":
        await message.answer("Расчёт отменён.", reply_markup=main_kb)
        await state.clear()
        return

    try:
        width = float(text.replace(",", "."))
        if width <= 0:
            raise ValueError()
        await state.update_data(width=width)
        dens_buttons = [KeyboardButton(text=f"{k} г/м²") for k in densities.keys()]
        dens_kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[dens_buttons, [KeyboardButton(text="⬅️ Назад"), KeyboardButton(text="❌ Отмена")]])
        await message.answer("Выберите плотность геотекстиля:", reply_markup=dens_kb)
        await state.set_state(CalcStates.waiting_for_density)
    except ValueError:
        await message.answer("Ошибка: ширина должна быть положительным числом. Попробуйте ещё раз.", reply_markup=cancel_back_kb)

@dp.message(CalcStates.waiting_for_density)async def process_density(message: types.Message, state: FSMContext):
    text = message.text
    if text == "⬅️ Назад":
        await message.answer("Введите ширину участка в метрах (например, 5):", reply_markup=cancel_back_kb)
        await state.set_state(CalcStates.waiting_for_width)
        return
    if text == "❌ Отмена":
        await message.answer("Расчёт отменён.", reply_markup=main_kb)
        await state.clear()
        return

    if text.replace(" г/м²", "") in densities:
        density = int(text.replace(" г/м²", ""))
        await state.update_data(density=density)
        await message.answer("Введите цену за квадратный метр (например, 50):", reply_markup=cancel_back_kb)
        await state.set_state(CalcStates.waiting_for_price)
    else:
        await message.answer("Пожалуйста, выберите плотность из списка.", reply_markup=cancel_back_kb)

@dp.message(CalcStates.waiting_for_price)
async def process_price(message: types.Message, state: FSMContext):
    text = message.text
    if text == "⬅️ Назад":
        density = (await state.get_data())["density"]
        dens_buttons = [KeyboardButton(text=f"{k} г/м²") for k in densities.keys()]
        dens_kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[dens_buttons, [KeyboardButton(text="⬅️ Назад"), KeyboardButton(text="❌ Отмена")]])
        await message.answer("Выберите плотность геотекстиля:", reply_markup=dens_kb)
        await state.set_state(CalcStates.waiting_for_density)
        return
    if text == "❌ Отмена":
        await message.answer("Расчёт отменён.", reply_markup=main_kb)
        await state.clear()
        return

    try:
        price = float(text.replace(",", "."))
        if price <= 0:
            raise ValueError()
        await state.update_data(price=price)

        data = await state.get_data()
        length = data["length"]
        width = data["width"]
        density = data["density"]

        area = length * width
        if area < 100:
            area *= 1.2  # +20% запас

        mass = area * (density / 1000)  # кг
        cost = area * price

        result = {
            "user_id": message.from_user.id,
            "length": length,
            "width": width,
            "density": density,
            "area": round(area, 2),
            "mass": round(mass, 2),
            "price_per_m2": price,
            "total_cost": round(cost, 2)
        }
        save_calculation(CALC_FILE, result)

        msg = (
            f"Результаты расчёта:\n"
            f"Площадь: {area:.2f} м²\n"
            f"Плотность: {density} г/м²\n"
            f"Масса: {mass:.2f} кг\n"
            f"Итоговая стоимость: {cost:.2f} ₽\n\n"
            f"Ваш расчёт сохранён."
        )
        await message.answer(msg, reply_markup=main_kb)
        await state.clear()
    except ValueError:
        await message.answer("Ошибка: цена должна быть положительным числом. Попробуйте ещё раз.", reply_markup=cancel_back_kb)

# --- Мои расчёты ---
@dp.message(Text(text="💾 Мои расчёты"))
async def my_calculations(message: types.Message):
    user_id = message.from_user.id
    all_calc = load_calculations(CALC_FILE)
    user_calc = [c for c in all_calc if c["user_id"] == user_id]

    if not user_calc:
        await message.answer("У вас ещё нет сохранённых расчётов.", reply_markup=main_kb)
        return

    texts = []
    for idx, c in enumerate(user_calc[-5:], 1):  # последние 5 расчетов
        texts.append(
            f"{idx}. Площадь: {c['area']} м², Плотность: {c['density']} г/м², Стоимость: {c['total_cost']} ₽"
        )
    await message.answer("Ваши последние расчёты:\n" + "\n".join(texts), reply_markup=main_kb)

# --- Советы и лайфхаки ---
@dp.message(Text(text="💡 Советы и лайфхаки"))
async def advices_handler(message: types.Message):
    await message.answer("\n".join(ADVICES), reply_markup=main_kb)

# --- Материалы ---
@dp.message(Text(text="📦 Материалы"))
async def materials_handler(message: types.Message):
    materials = (
        "📌 Геотекстиль — для фильтрации и разделения слоёв грунта.\n""📌 Геосетка — армирование и укрепление грунтов.\n"
        "📌 Биоматы — экологичная защита от эрозии.\n"
        "📌 Спанбонд — лёгкий укрывной материал.\n"
        "📌 Георешётка — для укрепления склона и дорожного покрытия."
    )
    await message.answer(materials, reply_markup=main_kb)

if __name__ == "__main__":
    import asyncio
    os.makedirs("data", exist_ok=True)
    asyncio.run(dp.start_polling(bot))

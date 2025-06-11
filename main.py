
import os
import logging

from dotenv import load_dotenv
load_dotenv()

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, Text
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

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
        [KeyboardButton("🔢 Сделать расчёт")],
        [KeyboardButton("💾 Мои расчёты")],
        [KeyboardButton("💡 Советы и лайфхаки")],
        [KeyboardButton("📦 Материалы")],
    ],
    resize_keyboard=True,
)

cancel_back_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton("⬅️ Назад"), KeyboardButton("❌ Отмена")]
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

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(f"Привет, {message.from_user.first_name}! Я помогу рассчитать нужное количество геотекстиля. Выберите действие:", reply_markup=main_kb)

if __name__ == "__main__":
    import asyncio
    os.makedirs("data", exist_ok=True)
    asyncio.run(dp.start_polling(bot))

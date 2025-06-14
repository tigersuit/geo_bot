import logging
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup

API_TOKEN = "7999512901:AAGg3X5JRAWzDm9GqkvnVR7ur14HVsKYYrc"

logging.basicConfig(level=logging.INFO)

# FSM
class CalcState(StatesGroup):
    waiting_for_quiz = State()
    waiting_for_length = State()
    waiting_for_density = State()

DENSITY_PRICES = {
    100: 50,
    150: 55,
    200: 60,
    250: 65,
    300: 70
}

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
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
    builder.button(text="💬 Задать вопрос")
    builder.button(text="📲 Заказать бота")  # ← Новая кнопка
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup(resize_keyboard=True)

@dp.message(F.text == "/start")
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        f"Привет, {message.from_user.first_name}! 👋\n"
        f"Я бот для расчёта геотекстиля (дорнита) и других материалов.\n\n"
        f"💡 Помогу подобрать плотность под задачу\n"
        f"📐 Рассчитаю площадь и цену\n"
        f"📦 Расскажу про материалы и лайфхаки\n"
        f"💬 Отвечу на вопросы — пиши в нашу группу: https://t.me/sva_fashion",
        reply_markup=main_menu()
    )

# Кнопка Задать вопрос
@dp.message(F.text == "💬 Задать вопрос")
async def ask_question(message: Message):
    await message.answer("Напиши свой вопрос в нашу группу:\nhttps://t.me/sva_fashion")

# Кнопка Сделать расчёт → сначала квиз
@dp.message(F.text == "🔢 Сделать расчёт")
async def start_quiz(message: Message, state: FSMContext):
    await state.set_state(CalcState.waiting_for_quiz)
    builder = ReplyKeyboardBuilder()
    builder.button(text="🚗 Парковка")
    builder.button(text="🏠 Отмостка")
    builder.button(text="💧 Дренаж")
    builder.button(text="👣 Дорожка")
    builder.adjust(2)
    await message.answer("Для чего вам нужен геотекстиль?", reply_markup=builder.as_markup(resize_keyboard=True))

@dp.message(CalcState.waiting_for_quiz)
async def quiz_answer(message: Message, state: FSMContext):
    mapping = {
        "🚗 Парковка": 250,
        "🏠 Отмостка": 150,
        "💧 Дренаж": 100,
        "👣 Дорожка": 150
    }
    recommended = mapping.get(message.text)
    if recommended:
        await message.answer(f"✅ Рекомендуем плотность: <b>{recommended} г/м²</b>")
    else:
        await message.answer("Выберите один из вариантов.")
        return
    await state.set_state(CalcState.waiting_for_length)
    await message.answer("Теперь введите длину участка в метрах:")

@dp.message(CalcState.waiting_for_length)
async def process_length(message: Message, state: FSMContext):
    try:
        length = float(message.text.replace(",", "."))
        await state.update_data(length=length)
        builder = ReplyKeyboardBuilder()
        for d in DENSITY_PRICES:
            builder.button(text=str(d))
        builder.adjust(3)
        await state.set_state(CalcState.waiting_for_density)
        await message.answer(
            "Выберите плотность из списка или введите свою (г/м²):",
            reply_markup=builder.as_markup(resize_keyboard=True)
        )
    except ValueError:
        await message.answer("Пожалуйста, введите число. Например: 12.5")

@dp.message(CalcState.waiting_for_density)
async def process_density(message: Message, state: FSMContext):
    try:
        density = int(message.text)
        if density not in DENSITY_PRICES:
            await message.answer("Плотность не из списка. Используем цену 0 ₽/м².")
            price_per_m2 = 0
        else:
            price_per_m2 = DENSITY_PRICES[density]

        data = await state.get_data()
        length = data["length"]
        width = 2
        area = length * width
        reserve_text = ""

        if area < 100:
            area *= 1.2
            reserve_text = "\n🔄 <i>Добавлен запас 20% (участок &lt; 100 м²)</i>"

        total_price = round(area * price_per_m2, 2)

        await message.answer(
            f"📏 Площадь: {area:.2f} м²\n"
            f"📦 Плотность: {density} г/м²\n"
            f"💰 Цена за м²: {price_per_m2} ₽\n"
            f"🧾 Итог: {total_price} ₽{reserve_text}",
            reply_markup=main_menu()
        )
        await state.clear()
    except ValueError:
        await message.answer("Введите число плотности или выберите из списка.")

@dp.message(F.text == "🔁 Новый расчёт")
async def new_calc(message: Message, state: FSMContext):
    await state.clear()
    await start_quiz(message, state)

@dp.message(F.text == "💾 Мои расчёты")
async def my_calcs(message: Message):
    await message.answer("🗂 История пока не сохраняется. Функция скоро появится!")
@dp.message(F.text == "💡 Советы и лайфхаки")
async def tips(message: Message):
    await message.answer(
        "💡 <b>Полезные советы и лайфхаки по использованию геотекстиля:</b>\n\n"
        "🔸 <b>1. Правильный выбор плотности:</b>\n"
        "▪ 100–150 г/м² — для дренажа и ландшафта\n"
        "▪ 150–200 г/м² — для садовых дорожек, отмостки\n"
        "▪ 200–300 г/м² — для парковки, проездов, дорог\n\n"
        "🔸 <b>2. Укладка:</b>\n"
        "▪ Утрамбуй основание (песок/грунт), убери крупные камни\n"
        "▪ Делай нахлёст 10–20 см между полотнами\n"
        "▪ Расположи материал внахлёст — поперёк направления движения\n\n"
        "🔸 <b>3. Геотекстиль + щебень:</b>\n"
        "▪ Всегда клади геотекстиль под щебень, чтобы избежать проседания\n"
        "▪ При дренажных работах оборачивай щебень полностью\n\n"
        "🔸 <b>4. Защита от сорняков:</b>\n"
        "▪ Используй спанбонд или дорнит 150 г/м² под щебень или плитку\n"
        "▪ Не экономь на качестве: тонкий материал может порваться\n\n"
        "🔸 <b>5. Частые ошибки:</b>\n"
        "❌ Укладка на грязную или неровную поверхность\n"
        "❌ Маленький нахлёст или отсутствие фиксации\n"
        "❌ Использование слишком тонкого материала под нагрузкой\n\n"
        "🔸 <b>6. Резка и фиксация:</b>\n"
        "▪ Режь строительным ножом или ножницами\n"
        "▪ Крепи геотекстиль анкерами или шпильками (через каждые 1–1.5 м)\n\n"
        "🔸 <b>7. Дополнительно:</b>\n"
        "▪ На склонах лучше использовать георешётку поверх геотекстиля\n"
        "▪ Для защиты склона от эрозии подойдут биоматы\n"
        "▪ Храни материал в сухом месте, защищённом от ультрафиолета\n\n"
        "📌 <i>Не уверен — пройди квиз в меню, и бот сам порекомендует нужную плотность!</i>"
    )

@dp.message(F.text == "📦 Материалы")
async def materials(message: Message):
    await message.answer(
        "<b>📦 Популярные материалы:</b>\n\n"
        "▪ <b>Геотекстиль (дорнит)</b> — разделение слоёв, армирование\n"
        "▪ <b>Геосетка</b> — усиление слабого основания\n"
        "▪ <b>Георешётка</b> — объёмное армирование склонов\n"
        "▪ <b>Биоматы</b> — защита от эрозии почвы\n"
        "▪ <b>Спанбонд</b> — для садоводов, защита от сорняков"
    )

@dp.message(F.text == "📝 Квиз")
async def quiz_shortcut(message: Message, state: FSMContext):
    await start_quiz(message, state)
    
@dp.message(F.text == "📲 Заказать бота")
async def order_bot(message: Message):
    await message.answer(
        "💼 Хочешь такого же бота под свой бизнес?\n"
        "Напиши мне прямо сейчас: @sva_fashion — расскажу, как он может увеличить твои продажи 🚀"
    )    

@dp.message()
async def unknown(message: Message, state: FSMContext):
    current = await state.get_state()
    if current in [CalcState.waiting_for_length, CalcState.waiting_for_density, CalcState.waiting_for_quiz]:
        return
    await message.answer("Не понимаю команду. Пожалуйста, выбери пункт меню.", reply_markup=main_menu())

# Запуск
if __name__ == "__main__":
    import asyncio
    asyncio.run(dp.start_polling(bot))

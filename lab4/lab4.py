import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.filters.command import Command
from dotenv import load_dotenv

load_dotenv()  # Загружает переменные из .env
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Получает токен

# Получение токена из переменного окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Словарь для хранения курсов валют
currencies = {}

# Состояния FSM


class CurrencyStates(StatesGroup):
    waiting_for_currency_name = State()
    waiting_for_currency_rate = State()
    waiting_for_convert_currency = State()
    waiting_for_convert_amount = State()

# Обработчики команд:

# /start


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я бот для конвертации валют.\n"
        "Чтобы продолжить, выберите одну из команд:\n"
        "/save_currency - сохранить курс валюты\n"
        "/convert - конвертировать валюту в рубли"
    )

# /save_currency


@dp.message(Command("save_currency"))
async def cmd_save_currency(message: types.Message, state: FSMContext):
    await message.answer("Введите название валюты (например, USD):")
    await state.set_state(CurrencyStates.waiting_for_currency_name)

# Обработчик названия валюты


@dp.message(CurrencyStates.waiting_for_currency_name)
async def process_currency_name(message: types.Message, state: FSMContext):
    currency_name = message.text.upper()
    await state.update_data(currency_name=currency_name)
    await message.answer(f"Введите курс {currency_name} к рублю:")
    await state.set_state(CurrencyStates.waiting_for_currency_rate)

# Обработчик курса валюты


@dp.message(CurrencyStates.waiting_for_currency_rate)
async def process_currency_rate(message: types.Message, state: FSMContext):
    try:
        rate = float(message.text)
        data = await state.get_data()
        currency_name = data["currency_name"]
        currencies[currency_name] = rate
        await message.answer(f"Курс {currency_name} сохранён: {rate} RUB")
        await state.clear()
    except ValueError:
        await message.answer("Ошибка! Введите число.")

# /convert


@dp.message(Command("convert"))
async def cmd_convert(message: types.Message, state: FSMContext):
    if not currencies:
        await message.answer("Нет сохранённых валют. Сначала используйте /save_currency.")
        return
    await message.answer("Введите название валюты для конвертации:")
    await state.set_state(CurrencyStates.waiting_for_convert_currency)

# Обработчик валюты для конвертации


@dp.message(CurrencyStates.waiting_for_convert_currency)
async def process_convert_currency(message: types.Message, state: FSMContext):
    currency_name = message.text.upper()
    if currency_name not in currencies:
        await message.answer("Эта валюта не сохранена. Попробуйте ещё раз.")
        return
    await state.update_data(currency_name=currency_name)
    await message.answer(f"Введите сумму в {currency_name}:")
    await state.set_state(CurrencyStates.waiting_for_convert_amount)

# Обработчик суммы и вывод результата


@dp.message(CurrencyStates.waiting_for_convert_amount)
async def process_convert_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        data = await state.get_data()
        currency_name = data["currency_name"]
        rate = currencies[currency_name]
        result = amount * rate
        await message.answer(f"{amount} {currency_name} = {result:.2f} RUB")
        await state.clear()
    except ValueError:
        await message.answer("Ошибка! Введите число.")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

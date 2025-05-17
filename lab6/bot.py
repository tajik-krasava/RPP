import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardBuilder
import requests
from dotenv import load_dotenv

load_dotenv()

# Конфигурация
BOT_TOKEN = os.getenv("BOT_TOKEN")
CURRENCY_SERVICE_URL = "http://localhost:5001"
DATA_SERVICE_URL = "http://localhost:5002"

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# Состояния FSM
class CurrencyStates(StatesGroup):
    waiting_for_currency_name = State()
    waiting_for_currency_rate = State()
    waiting_for_delete_currency = State()
    waiting_for_convert_currency = State()
    waiting_for_convert_amount = State()


# Клавиатуры
def get_main_kb():
    builder = ReplyKeyboardBuilder()
    builder.add(
        types.KeyboardButton(text="/manage_currency"),
        types.KeyboardButton(text="/get_currencies"),
        types.KeyboardButton(text="/convert")
    )
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def get_manage_kb():
    builder = ReplyKeyboardBuilder()
    builder.add(
        types.KeyboardButton(text="Добавить валюту"),
        types.KeyboardButton(text="Удалить валюту"),
        types.KeyboardButton(text="Изменить курс валюты"),
        types.KeyboardButton(text="Назад")
    )
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


# Обработчики команд
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Выберите команду:", reply_markup=get_main_kb())


@dp.message(Command("manage_currency"))
async def cmd_manage_currency(message: types.Message):
    await message.answer("Выберите действие:", reply_markup=get_manage_kb())


@dp.message(F.text == "Назад")
async def back_to_main(message: types.Message):
    await message.answer("Главное меню:", reply_markup=get_main_kb())


# Добавление валюты
@dp.message(F.text == "Добавить валюту")
async def add_currency_start(message: types.Message, state: FSMContext):
    await message.answer("Введите название валюты:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(CurrencyStates.waiting_for_currency_name)
    await state.update_data(action="add")


@dp.message(CurrencyStates.waiting_for_currency_name, F.text)
async def process_currency_name(message: types.Message, state: FSMContext):
    data = await state.get_data()

    if data.get("action") == "add":
        # Проверка существования валюты
        response = requests.get(f"{DATA_SERVICE_URL}/currencies")
        if response.status_code == 200:
            currencies = response.json().get("currencies", [])
            for currency in currencies:
                if currency["currency_name"].lower() == message.text.lower():
                    await message.answer(
                        "Данная валюта уже существует",
                        reply_markup=get_manage_kb()
                    )
                    await state.clear()
                    return

    await state.update_data(currency_name=message.text)
    await message.answer("Введите курс к рублю:")
    await state.set_state(CurrencyStates.waiting_for_currency_rate)


@dp.message(CurrencyStates.waiting_for_currency_rate, F.text)
async def process_currency_rate(message: types.Message, state: FSMContext):
    try:
        rate = float(message.text)
        data = await state.get_data()
        currency_name = data["currency_name"]
        action = data["action"]

        if action == "add":
            response = requests.post(
                f"{CURRENCY_SERVICE_URL}/load",
                json={"currency_name": currency_name, "rate": rate},
            )
            if response.status_code == 200:
                await message.answer(
                    f"Валюта: {currency_name} успешно добавлена",
                    reply_markup=get_manage_kb()
                )
        elif action == "update":
            response = requests.post(
                f"{CURRENCY_SERVICE_URL}/update_currency",
                json={"currency_name": currency_name, "new_rate": rate},
            )
            if response.status_code == 200:
                await message.answer(
                    f"Курс валюты {currency_name} успешно обновлен",
                    reply_markup=get_manage_kb()
                )

        await state.clear()
    except ValueError:
        await message.answer("Пожалуйста, введите число:")


# Удаление валюты
@dp.message(F.text == "Удалить валюту")
async def delete_currency_start(message: types.Message, state: FSMContext):
    await message.answer(
        "Введите название валюты для удаления:",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(CurrencyStates.waiting_for_delete_currency)


@dp.message(CurrencyStates.waiting_for_delete_currency, F.text)
async def process_delete_currency(message: types.Message, state: FSMContext):
    currency_name = message.text
    response = requests.post(
        f"{CURRENCY_SERVICE_URL}/delete",
        json={"currency_name": currency_name},
    )

    if response.status_code == 200:
        await message.answer(
            f"Валюта {currency_name} успешно удалена",
            reply_markup=get_manage_kb()
        )
    else:
        await message.answer(
            "Валюта не найдена или произошла ошибка",
            reply_markup=get_manage_kb()
        )

    await state.clear()


# Изменение курса
@dp.message(F.text == "Изменить курс валюты")
async def update_currency_start(message: types.Message, state: FSMContext):
    await message.answer("Введите название валюты:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(CurrencyStates.waiting_for_currency_name)
    await state.update_data(action="update")


# Получение списка валют
@dp.message(Command("get_currencies"))
async def cmd_get_currencies(message: types.Message):
    response = requests.get(f"{DATA_SERVICE_URL}/currencies")
    if response.status_code == 200:
        currencies = response.json().get("currencies", [])
        if currencies:
            message_text = "Список валют:\n" + "\n".join(
                [f"{c['currency_name']}: {c['rate']} RUB" for c in currencies]
            )
        else:
            message_text = "Нет доступных валют"
    else:
        message_text = "Ошибка при получении списка валют"

    await message.answer(message_text, reply_markup=get_main_kb())


# Конвертация валюты
@dp.message(Command("convert"))
async def cmd_convert(message: types.Message, state: FSMContext):
    await message.answer(
        "Введите название валюты:",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(CurrencyStates.waiting_for_convert_currency)


@dp.message(CurrencyStates.waiting_for_convert_currency, F.text)
async def process_convert_currency(message: types.Message, state: FSMContext):
    await state.update_data(currency=message.text)
    await message.answer("Введите сумму:")
    await state.set_state(CurrencyStates.waiting_for_convert_amount)


@dp.message(CurrencyStates.waiting_for_convert_amount, F.text)
async def process_convert_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text)
        data = await state.get_data()
        currency = data["currency"]

        response = requests.get(
            f"{DATA_SERVICE_URL}/convert",
            params={"currency": currency, "amount": amount},
        )

        if response.status_code == 200:
            result = response.json()
            await message.answer(
                f"{amount} {currency} = {result['converted_amount']} RUB",
                reply_markup=get_main_kb()
            )
        else:
            await message.answer(
                "Ошибка конвертации. Проверьте название валюты.",
                reply_markup=get_main_kb()
            )

        await state.clear()
    except ValueError:
        await message.answer("Пожалуйста, введите число:")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
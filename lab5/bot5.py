import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.filters.command import Command
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    BotCommand,
    BotCommandScopeDefault,
    BotCommandScopeChat
)
from dotenv import load_dotenv
import psycopg2

load_dotenv()

# Выгрузка токена из виртуального окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Подключаем данные из виртуального окружения


def get_db_connection():
    return psycopg2.connect(
        host=os.environ['DB_HOST'],
        port=os.environ['DB_PORT'],
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD'],
        database=os.environ['DB_NAME']
    )

# Инициализация базы данных


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    conn.commit()
    cur.close()
    conn.close()

# Проверка на права администратора


def is_admin(chat_id: str) -> bool:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM admins WHERE chat_id = %s", (str(chat_id),))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result is not None

# Состояния FSM


class CurrencyStates(StatesGroup):
    waiting_for_currency_name = State()
    waiting_for_currency_rate = State()
    waiting_for_convert_currency = State()
    waiting_for_convert_amount = State()
    waiting_for_manage_action = State()
    waiting_for_add_name = State()
    waiting_for_add_rate = State()
    waiting_for_delete_name = State()
    waiting_for_update_name = State()
    waiting_for_update_rate = State()


# Команды для разных пользователей
admin_commands = [
    BotCommand(command="start", description="Начать работу"),
    BotCommand(command="manage_currency", description="Управление валютами - администратор"),
    BotCommand(command="get_currencies", description="Список всех валют"),
    BotCommand(command="convert", description="Конвертация валют"),
]

user_commands = [
    BotCommand(command="start", description="Начать работу"),
    BotCommand(command="get_currencies", description="Список всех валют"),
    BotCommand(command="convert", description="Конвертация валют"),
]

# Функция для установки команд бота


async def setup_bot_commands():
    await bot.set_my_commands(user_commands, scope=BotCommandScopeDefault())

    # Устанавливаем команды для всех админов
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT chat_id FROM admins")
    admin_chat_ids = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()

    for chat_id in admin_chat_ids:
        await bot.set_my_commands(
            admin_commands,
            scope=BotCommandScopeChat(chat_id=chat_id)
        )

# Команда /start


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if is_admin(message.chat.id):
        await message.answer(
            "Привет, я бот для конвертации валют(Вы обладаете правами администратора).\n"
            "Доступные команды:\n"
            "/manage_currency - управление валютами\n"
            "/get_currencies - список всех валют\n"
            "/convert - конвертировать валюту в рубли"
        )
    else:
        await message.answer(
            "Привет! Я бот для конвертации валют.\n"
            "Доступные команды:\n"
            "/get_currencies - список всех валют\n"
            "/convert - конвертировать валюту в рубли"
        )

# Команда /get_currencies


@dp.message(Command("get_currencies"))
async def cmd_get_currencies(message: types.Message):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT currency_name, rate FROM currencies ORDER BY currency_name")
    currencies = cur.fetchall()
    cur.close()
    conn.close()

    if not currencies:
        await message.answer("Нет доступных валют.")
        return

    response = "Список доступных валют:\n"
    for currency in currencies:
        response += f"{currency[0]}: {currency[1]} RUB\n"

    await message.answer(response)

# Команда /convert


@dp.message(Command("convert"))
async def cmd_convert(message: types.Message, state: FSMContext):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT currency_name FROM currencies")
    if not cur.fetchall():
        await message.answer("Нет доступных валют. Необходимо добавить валюту.")
        cur.close()
        conn.close()
        return

    await message.answer("Введите название валюты для конвертации:")
    await state.set_state(CurrencyStates.waiting_for_convert_currency)


@dp.message(CurrencyStates.waiting_for_convert_currency)
async def process_convert_currency(message: types.Message, state: FSMContext):
    currency_name = message.text.upper()

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT rate FROM currencies WHERE currency_name = %s", (currency_name,))
    result = cur.fetchone()
    cur.close()
    conn.close()

    if not result:
        await message.answer("Данная валюта не найдена")
        return

    await state.update_data(currency_name=currency_name, rate=result[0])
    await message.answer(f"Введите сумму в {currency_name}:")
    await state.set_state(CurrencyStates.waiting_for_convert_amount)


@dp.message(CurrencyStates.waiting_for_convert_amount)
async def process_convert_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.replace(',', '.'))
        data = await state.get_data()
        currency_name = data["currency_name"]
        rate = float(data["rate"])
        result = amount * rate
        await message.answer(f"{amount} {currency_name} = {result:.2f} RUB")
        await state.clear()
    except ValueError:
        await message.answer("Ошибка, попробуйте заново")

# Настройка команды /manage_currency
@dp.message(Command("manage_currency"))
async def cmd_manage_currency(message: types.Message):
    if not is_admin(message.chat.id):
        await message.answer("Нет доступа к команде")
        return

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Добавить валюту"),
                KeyboardButton(text="Удалить валюту"),
                KeyboardButton(text="Изменить курс валюты"),
            ]
        ],
        resize_keyboard=True
    )

    await message.answer(
        "Доступные действия:",
        reply_markup=keyboard
    )

# Обработка кнопки "Добавить валюту"


@dp.message(F.text == "Добавить валюту")
async def add_currency_start(message: types.Message, state: FSMContext):
    await message.answer(
        "Введите название валюты:",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(CurrencyStates.waiting_for_add_name)


@dp.message(CurrencyStates.waiting_for_add_name)
async def add_currency_name(message: types.Message, state: FSMContext):
    currency_name = message.text.upper()

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM currencies WHERE currency_name = %s",
                (currency_name,))
    if cur.fetchone():
        await message.answer("Данная валюта уже существует")
        cur.close()
        conn.close()
        await state.clear()
        return

    await state.update_data(currency_name=currency_name)
    await message.answer(f"Введите курс {currency_name} к рублю:")
    await state.set_state(CurrencyStates.waiting_for_add_rate)


@dp.message(CurrencyStates.waiting_for_add_rate)
async def add_currency_rate(message: types.Message, state: FSMContext):
    try:
        rate = float(message.text.replace(',', '.'))
    except ValueError:
        await message.answer("Введите число")
        return

    data = await state.get_data()
    currency_name = data['currency_name']

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO currencies (currency_name, rate) VALUES (%s, %s)",
        (currency_name, rate)
    )
    conn.commit()
    cur.close()
    conn.close()

    await message.answer(f"Валюта: {currency_name} успешно добавлена")
    await state.clear()

# Обработка кнопки "Удалить валюту"


@dp.message(F.text == "Удалить валюту")
async def delete_currency_start(message: types.Message, state: FSMContext):
    await message.answer(
        "Введите название валюты для удаления:",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(CurrencyStates.waiting_for_delete_name)


@dp.message(CurrencyStates.waiting_for_delete_name)
async def delete_currency(message: types.Message, state: FSMContext):
    currency_name = message.text.upper()

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM currencies WHERE currency_name = %s",
                (currency_name,))
    deleted_rows = cur.rowcount
    conn.commit()
    cur.close()
    conn.close()

    if deleted_rows > 0:
        await message.answer(f"Валюта {currency_name} успешно удалена")
    else:
        await message.answer(f"Валюта {currency_name} не найдена")

    await state.clear()

# Обработка кнопки "Изменить курс валюты"


@dp.message(F.text == "Изменить курс валюты")
async def update_currency_start(message: types.Message, state: FSMContext):
    await message.answer(
        "Введите название валюты:",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(CurrencyStates.waiting_for_update_name)


@dp.message(CurrencyStates.waiting_for_update_name)
async def update_currency_name(message: types.Message, state: FSMContext):
    currency_name = message.text.upper()

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM currencies WHERE currency_name = %s",
                (currency_name,))
    if not cur.fetchone():
        await message.answer("Данная валюта не существует")
        cur.close()
        conn.close()
        await state.clear()
        return

    await state.update_data(currency_name=currency_name)
    await message.answer("Введите новый курс к рублю:")
    await state.set_state(CurrencyStates.waiting_for_update_rate)


@dp.message(CurrencyStates.waiting_for_update_rate)
async def update_currency_rate(message: types.Message, state: FSMContext):
    try:
        rate = float(message.text.replace(',', '.'))
    except ValueError:
        await message.answer("Введите число")
        return

    data = await state.get_data()
    currency_name = data['currency_name']

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE currencies SET rate = %s WHERE currency_name = %s",
        (rate, currency_name)
    )
    conn.commit()
    cur.close()
    conn.close()

    await message.answer(f"Курс валюты {currency_name} успешно изменен")
    await state.clear()

# Запуск бота


async def main():
    init_db()  # Инициализация базы данных
    await setup_bot_commands()  # Установка команд бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

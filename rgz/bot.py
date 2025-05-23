import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove
from dotenv import load_dotenv
import psycopg2
import requests
from datetime import datetime

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

DB_CONFIG = {
    'host': os.environ['DB_HOST'],
    'port': os.environ['DB_PORT'],
    'user': os.environ['DB_USER'],
    'password': os.environ['DB_PASSWORD'],
    'database': os.environ['DB_NAME']
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

# Состояния FSM
class RegStates(StatesGroup):
    waiting_for_name = State()

class OperationStates(StatesGroup):
    waiting_for_operation_type = State()
    waiting_for_sum = State()
    waiting_for_date = State()

class ViewOperationsStates(StatesGroup):
    waiting_for_currency = State()

# Проверка регистрации
def is_registered(chat_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE id = %s", (chat_id,))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result is not None

# Команда /start с настройкой меню
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Устанавливаем команды меню
    await bot.set_my_commands([
        types.BotCommand(command="start", description="Главное меню"),
        types.BotCommand(command="reg", description="Регистрация"),
        types.BotCommand(command="add_operation", description="Добавить операцию"),
        types.BotCommand(command="operations", description="Мои операции"),
        types.BotCommand(command="delaccount", description="Удалить аккаунт")
    ])
    await message.answer(
        "Привет! Я финансовый бот.\n\n"
        "Доступные команды:\n"
        "/reg — регистрация\n"
        "/add_operation — новая операция\n"
        "/operations — просмотр операций\n"
        "/delaccount — удалить аккаунт\n\n"
        "Используйте меню слева для быстрого доступа к командам.",
        reply_markup=ReplyKeyboardRemove()
    )

# Команда /reg
@dp.message(Command("reg"))
async def cmd_reg(message: types.Message, state: FSMContext):
    if is_registered(message.chat.id):
        await message.answer("Вы уже зарегистрированы.")
        return
    
    await message.answer("Введите ваше имя:")
    await state.set_state(RegStates.waiting_for_name)

@dp.message(RegStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(
            "INSERT INTO users (id, name) VALUES (%s, %s)",
            (message.chat.id, message.text)
        )
        conn.commit()
        await message.answer("Регистрация успешна!")
    except psycopg2.IntegrityError:
        await message.answer("Вы уже зарегистрированы!")
    finally:
        cur.close()
        conn.close()
    
    await state.clear()

# Команда /add_operation
@dp.message(Command("add_operation"))
async def cmd_add_operation(message: types.Message, state: FSMContext):
    if not is_registered(message.chat.id):
        await message.answer("Сначала зарегистрируйтесь с помощью /reg")
        return

    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="РАСХОД"), types.KeyboardButton(text="ДОХОД")]
        ],
        resize_keyboard=True
    )

    await message.answer("Выберите тип операции:", reply_markup=keyboard)
    await state.set_state(OperationStates.waiting_for_operation_type)

@dp.message(OperationStates.waiting_for_operation_type)
async def process_operation_type(message: types.Message, state: FSMContext):
    if message.text not in ["РАСХОД", "ДОХОД"]:
        await message.answer("Пожалуйста, выберите один из предложенных вариантов.")
        return
    await state.update_data(type_operation=message.text)
    await message.answer("Введите сумму операции (в рублях):", reply_markup=ReplyKeyboardRemove())
    await state.set_state(OperationStates.waiting_for_sum)

@dp.message(OperationStates.waiting_for_sum)
async def process_operation_sum(message: types.Message, state: FSMContext):
    try:
        sum_value = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Пожалуйста, введите число.")
        return
    await state.update_data(sum=sum_value)
    await message.answer("Введите дату операции в формате ГГГГ-ММ-ДД:")
    await state.set_state(OperationStates.waiting_for_date)

@dp.message(OperationStates.waiting_for_date)
async def process_operation_date(message: types.Message, state: FSMContext):
    try:
        date_value = datetime.strptime(message.text, "%Y-%m-%d").date()
    except ValueError:
        await message.answer("Неверный формат даты. Используйте ГГГГ-ММ-ДД.")
        return

    data = await state.get_data()

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO operations (date, sum, chat_id, type_operation) VALUES (%s, %s, %s, %s)",
            (date_value, data["sum"], message.chat.id, data["type_operation"])
        )
        conn.commit()
        await message.answer("Операция успешно добавлена!")
    except Exception as e:
        await message.answer(f"Произошла ошибка: {e}")
    finally:
        cur.close()
        conn.close()
        await state.clear()

# Команда /operations
@dp.message(Command("operations"))
async def cmd_operations(message: types.Message, state: FSMContext):
    if not is_registered(message.chat.id):
        await message.answer("Сначала зарегистрируйтесь с помощью /reg")
        return

    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="RUB"), types.KeyboardButton(text="USD"), types.KeyboardButton(text="EUR")]
        ],
        resize_keyboard=True
    )

    await message.answer("Выберите валюту для отображения операций:", reply_markup=keyboard)
    await state.set_state(ViewOperationsStates.waiting_for_currency)

@dp.message(ViewOperationsStates.waiting_for_currency)
async def process_currency(message: types.Message, state: FSMContext):
    if message.text not in ["RUB", "USD", "EUR"]:
        await message.answer("Пожалуйста, выберите одну из предложенных валют.")
        return

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT date, sum, type_operation FROM operations WHERE chat_id = %s ORDER BY date DESC",
            (message.chat.id,)
        )
        operations = cur.fetchall()

        if not operations:
            await message.answer("У вас пока нет операций.")
            return

        response_text = "Ваши операции:\n\n"
        
        if message.text == "RUB":
            for op in operations:
                response_text += f"{op[0].strftime('%Y-%m-%d')} | {op[1]:.2f} RUB | {op[2]}\n"
        else:
            try:
                response = requests.get(f"http://localhost:5000/rate?currency={message.text}")
                rate = float(response.json()["rate"])
                
                for op in operations:
                    converted = float(op[1]) / rate
                    response_text += f"{op[0].strftime('%Y-%m-%d')} | {converted:.2f} {message.text} | {op[2]}\n"
            except Exception as e:
                await message.answer(f"Не удалось получить курс валюты. Ошибка: {e}")
                return

        await message.answer(response_text)
    except Exception as e:
        await message.answer(f"Произошла ошибка: {e}")
    finally:
        cur.close()
        conn.close()
        await state.clear()

# Команда /delaccount
@dp.message(Command("delaccount"))
async def cmd_delete_account(message: types.Message):
    if not is_registered(message.chat.id):
        await message.answer("Вы не зарегистрированы.")
        return

    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("DELETE FROM operations WHERE chat_id = %s", (message.chat.id,))
        cur.execute("DELETE FROM users WHERE id = %s", (message.chat.id,))
        conn.commit()
        await message.answer("Ваш аккаунт и все данные успешно удалены!")
    except Exception as e:
        conn.rollback()
        await message.answer(f"Ошибка при удалении аккаунта: {e}")
    finally:
        cur.close()
        conn.close()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
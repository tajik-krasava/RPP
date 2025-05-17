from flask import Flask, request, jsonify
import psycopg2
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

app = Flask(__name__)

# Конфигурация подключения к БД через переменные окружения
DB_CONFIG = {
    'host': os.environ['DB_HOST'],
    'port': os.environ['DB_PORT'],
    'user': os.environ['DB_USER'],
    'password': os.environ['DB_PASSWORD'],
    'database': os.environ['DB_NAME']
}


def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

@app.after_request
def add_charset(response):
    response.headers["Content-Type"] = "application/json; charset=utf-8"
    return response


@app.route('/load', methods=['POST'])
def load_currency():
    data = request.get_json()
    currency_name = data.get('currency_name')
    rate = data.get('rate')

    if not currency_name or not rate:
        return jsonify({'error': 'Необходимо указать currency_name и rate'}), 400

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM currencies WHERE currency_name = %s",
                    (currency_name,)
                )
                if cur.fetchone():
                    return jsonify({'error': 'Валюта уже существует'}), 400

                cur.execute(
                    "INSERT INTO currencies (currency_name, rate) VALUES (%s, %s)",
                    (currency_name, rate)
                )
                conn.commit()
        return jsonify({'message': 'Валюта успешно добавлена'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/update_currency', methods=['POST'])
def update_currency():
    data = request.get_json()
    currency_name = data.get('currency_name')
    new_rate = data.get('new_rate')

    if not currency_name or not new_rate:
        return jsonify({'error': 'Необходимо указать currency_name и new_rate'}), 400

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM currencies WHERE currency_name = %s",
                    (currency_name,)
                )
                if not cur.fetchone():
                    return jsonify({'error': 'Валюта не найдена'}), 404

                cur.execute(
                    "UPDATE currencies SET rate = %s WHERE currency_name = %s",
                    (new_rate, currency_name)
                )
                conn.commit()
        return jsonify({'message': 'Курс валюты успешно обновлен'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/delete', methods=['POST'])
def delete_currency():
    data = request.get_json()
    currency_name = data.get('currency_name')

    if not currency_name:
        return jsonify({'error': 'Необходимо указать currency_name'}), 400

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM currencies WHERE currency_name = %s",
                    (currency_name,)
                )
                if not cur.fetchone():
                    return jsonify({'error': 'Валюта не найдена'}), 404

                cur.execute(
                    "DELETE FROM currencies WHERE currency_name = %s",
                    (currency_name,)
                )
                conn.commit()
        return jsonify({'message': 'Валюта успешно удалена'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(port=5001, debug=True)
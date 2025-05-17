from flask import Flask, request, jsonify
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

DB_CONFIG = {
    'host': os.environ['DB_HOST'],
    'port': os.environ['DB_PORT'],
    'user': os.environ['DB_USER'],
    'password': os.environ['DB_PASSWORD'],
    'database': os.environ['DB_NAME']
}


def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


@app.route('/convert', methods=['GET'])
def convert_currency():
    currency_name = request.args.get('currency')
    amount = request.args.get('amount')

    if not currency_name or not amount:
        return jsonify({'error': 'Необходимо указать currency и amount'}), 400

    try:
        amount = float(amount)
    except ValueError:
        return jsonify({'error': 'Amount должен быть числом'}), 400

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # Получаем курс валюты
                cur.execute(
                    "SELECT rate FROM currencies WHERE currency_name = %s",
                    (currency_name,)
                )
                result = cur.fetchone()

                if not result:
                    return jsonify({'error': 'Валюта не найдена'}), 404

                rate = float(result[0])
                converted_amount = round(amount * rate, 2)

                return jsonify({
                    'original_amount': amount,
                    'currency': currency_name,
                    'rate': rate,
                    'converted_amount': converted_amount
                }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/currencies', methods=['GET'])
def get_all_currencies():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT currency_name, rate FROM currencies")
                currencies = cur.fetchall()

                result = [{
                    'currency_name': currency[0],
                    'rate': float(currency[1])
                } for currency in currencies]

                return jsonify({'currencies': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(port=5002, debug=True)
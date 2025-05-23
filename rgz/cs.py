from flask import Flask, request, jsonify

app = Flask(__name__)

rates = {
    "USD": 79.5,
    "EUR": 90.2
}

@app.route("/rate")
def get_rate():
    currency = request.args.get("currency")
    if not currency:
        return jsonify({"message": "UNKNOWN CURRENCY"}), 400

    if currency not in rates:
        return jsonify({"message": "UNKNOWN CURRENCY"}), 400

    try:
        return jsonify({"rate": rates[currency]}), 200
    except Exception:
        return jsonify({"message": "UNEXPECTED ERROR"}), 500

if __name__ == "__main__":
    app.run(port=5000)
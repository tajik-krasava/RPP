from flask import Flask, request, jsonify
import random

app = Flask(__name__)

@app.route('/number/', methods=['GET'])
def get_number():
    param = int(request.args.get('param'))
    random_num = random.randint(0, 100)
    result = random_num * param
    return jsonify({'json_param': param,"result": result, "operation": "*", "random_num": random_num}) 


@app.route('/number/', methods=['POST'])
def post_number():
    data = request.get_json()
    json_param = data.get('jsonParam') 
    random_num = random.randint(0, 100)
    operation = random.choice(['+', '-', '*', '/'])  
    
    if operation == "+":
        result = random_num + json_param
    elif operation == "-":
        result = random_num - json_param
    elif operation == "*":
        result = random_num * json_param
    elif operation == "/":
        if json_param == 0:
            return jsonify({"error": "Division by zero!"}), 400
        result = random_num / json_param

    return jsonify({
        'json_param': json_param,
        "random_number": random_num,
        "operation": operation,  
        "result": result
    })    


@app.route('/number/', methods=['DELETE'])
def delete_number():
    random_number = random.random()
    operations = ['+', '-', '*', '/']
    operation = random.choice(operations)
    json_param = random.random()
    if operation == "+":
        result = random_number + json_param
    elif operation == "-":
        result = random_number - json_param
    elif operation == "*":
        result = random_number * json_param
    elif operation == "/":
        if json_param == 0:
            return jsonify({"error": "Division by zero!"}), 400
        result = random_number / json_param

    return jsonify({'json_param': json_param, 
                    'random_number': random_number, 
                    'result': result, 
                    'operation': operation})


if __name__ == '__main__':
    app.run(debug=True)
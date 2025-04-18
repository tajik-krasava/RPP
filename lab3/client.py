import requests
import random


URL = "http://127.0.0.1:5000"


param = random.randint(1, 10)
get_response = requests.get(f"{URL}/number/?param={param}")
get_data = get_response.json()

if "number" not in get_data:
    num1 = get_data["result"] / param
    multiply = "*"
else:
    num1 = get_data["number"]
    multiply = get_data.get("operation", "*")

print(f"GET: {num1} {multiply} {param} = {get_data['result']}")


json_param = random.randint(1, 10)
post_response = requests.post(
    f"{URL}/number/",
    json={"jsonParam": json_param},
    headers={"Content-Type": "application/json"}
)
post_data = post_response.json()
num2 = post_data["random_number"]
calc = post_data["operation"]

print(f"POST: {num2} {calc} {json_param} = {post_data['result']}")


delete_response = requests.delete(f'{URL}/number/')
delete_data = delete_response.json()
num3 = delete_data["random_number"]
delete = delete_data["operation"]

print(f"DELETE: {num3} {delete} ?")


expression = f"({num1} {multiply} {param}) {calc} ({num2} {delete} {num3})"
result = eval(expression)
final_result = int(round(result))

print("\nИтоговое выражение:", expression)
print("Результат (int):", final_result)


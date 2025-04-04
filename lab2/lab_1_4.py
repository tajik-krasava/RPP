import sys

data_input = sys.stdin.readline().strip()

numbers = []
current_number = ''
for char in data_input:
    if char == ' ':
        if current_number:
            numbers.append(int(current_number))
            current_number = ''
    else:
        current_number += char
if current_number:
    numbers.append(int(current_number))

sum = 0
count = 0

i = 0
while i < len(numbers):
    sum += numbers[i]
    count += 1
    i += 1

print(f"Сумма всех чисел: {sum}")
print(f"Количество всех чисел: {count}")
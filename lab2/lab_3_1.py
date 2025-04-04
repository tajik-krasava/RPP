import sys

# 1. Считываем массив из аргументов командной строки
arr = []
for i in range(1, len(sys.argv)):
    arr.append(int(sys.argv[i]))

print("Исходный массив:", arr)

# 2. Находим максимальный элемент
max_el = arr[0]
for num in arr:
    if num > max_el:
        max_el = num
print("Максимальный элемент:", max_el)

# 3. Выводим массив в обратном порядке
reversed_arr = arr[::-1]
print("Массив в обратном порядке:", reversed_arr)

# 6. Заменяем нули на среднее арифметическое
sum_el = 0
count = 0
for num in arr:
    sum_el += num
    count += 1
average = sum_el / count

new_arr = []
for num in arr:
    if num == 0:
        new_arr.append(average)
    else:
        new_arr.append(num)

print("Массив после замены нулей:", new_arr)
vvod_stroki = input("Введите строку: ")

count = 0
word_start = True

for char in vvod_stroki:
    if word_start and (char in ('m', 'M', 'м', 'М')):
        count += 1
        word_start = False
    elif char == ' ':
        word_start = True
    else:
        word_start = False

print("Количество слов на 'm'/'м':", count)
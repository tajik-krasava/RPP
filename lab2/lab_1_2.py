import sys


num1 = float(sys.stdin.readline().strip())
num2 = float(sys.stdin.readline().strip())
num3 = float(sys.stdin.readline().strip())


numbers = [num1, num2, num3]
for num in numbers:
    if 1 <= num <= 50:
        print(f"Число {num} попадает в нужный интервал")
    else:
        print(f"Число {num} не попадает в нужный интервал")

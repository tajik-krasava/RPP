import sys


num1 = float(sys.stdin.readline().strip())
num2 = float(sys.stdin.readline().strip())
num3 = float(sys.stdin.readline().strip())


min_num = min(num1, num2, num3)


print(f"Минимальное число: {min_num}")
import sys


m = float(sys.stdin.readline().strip())

for i in range(1, 11):
    print(f"{i} * {m} = {i * m}")
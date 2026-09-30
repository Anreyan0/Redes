with open("file_test.txt", "w") as file:
    for i in range(16):
        file.write("1" * i + "-" * (16 - i))
# SERVER
import socket_tcp

address = ("localhost", 5000)

server_socketTCP = socket_tcp.SocketTCP()
server_socketTCP.bind(address)
connection_socketTCP, new_address = server_socketTCP.accept()

# test 1
buff_size = 16
full_message = connection_socketTCP.recv(buff_size)
print("Test 1 received:", full_message)
if full_message == "Mensje de len=16".encode(): print("Test 1: Passed")
else: print("Test 1: Failed")

# test 2
buff_size = 19
full_message = connection_socketTCP.recv(buff_size)
print("Test 2 received:", full_message)
if full_message == "Mensaje de largo 19".encode(): print("Test 2: Passed")
else: print("Test 2: Failed")

# test 3
buff_size = 14
message_part_1 = connection_socketTCP.recv(buff_size)
message_part_2 = connection_socketTCP.recv(buff_size)
print("Test 3 received:", message_part_1 + message_part_2)
if (message_part_1 + message_part_2) == "Mensaje de largo 19".encode(): print("Test 3: Passed")
else: print("Test 3: Failed")

# test 4
buff_size = 24
message_part_1 = connection_socketTCP.recv(buff_size)
print("Test 4 received:", message_part_1)
if (message_part_1) == "Mensaje de largo 19".encode(): print("Test 4: Passed\n")
else: print("Test 4: Failed")


# test 5
buff_size = 14
message_part_1 = connection_socketTCP.recv(buff_size) # 14
print(message_part_1)
message_part_2 = connection_socketTCP.recv(buff_size) # 28
print(message_part_2)
message_part_3 = connection_socketTCP.recv(buff_size) # 42
print(message_part_3)
message_part_4 = connection_socketTCP.recv(buff_size) # 56
print(message_part_4)
message_part_5 = connection_socketTCP.recv(buff_size) # 70
print(message_part_5)
message_part_6 = connection_socketTCP.recv(buff_size) # 72
print(message_part_6)
complete_message = message_part_1 + message_part_2 + message_part_3 + message_part_4 + message_part_5 + message_part_6
print("Test 5 received:", complete_message)
if (complete_message) == "Esto entre muchas comillas se supone que debe ser un mensaje de largo 72".encode(): 
    print("Test 5: Passed")
else: 
    print("Test 5: Failed")
    print(len("Esto entre muchas comillas se supone que debe ser un mensaje de largo 72"))

# test 6
buff_size = 14
message_part_1 = connection_socketTCP.recv(buff_size)
message_part_2 = connection_socketTCP.recv(buff_size)
message_part_3 = connection_socketTCP.recv(buff_size)
message_part_4 = connection_socketTCP.recv(buff_size)
complete_message = message_part_1 + message_part_2 + message_part_3 + message_part_4
print("Test 6 received:", complete_message)
if (complete_message) == "Esto entre muchas comillas es un mensaje de largo 52".encode(): 
    print("Test 6: Passed")
else: 
    print("Test 6: Failed")


print("Cerrando conexión")
connection_socketTCP.recv_close()
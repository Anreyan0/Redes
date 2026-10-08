import socket_tcp

address = ("localhost", 5000)


# CLIENT
client_socketTCP = socket_tcp.SocketTCP()
client_socketTCP.connect(address)
# test 1
message = "Mensje de len=16".encode()
client_socketTCP.send(message)
# test 2
message = "Mensaje de largo 19".encode()
client_socketTCP.send(message)
# test 3
message = "Mensaje de largo 19".encode()
client_socketTCP.send(message)
# test 4
message = "Mensaje de largo 19".encode()
client_socketTCP.send(message)

# tests largos
print("Empiezan los tests largos")


# test 5
message = "Esto entre muchas comillas se supone que debe ser un mensaje de largo 72".encode()
client_socketTCP.send(message)
# test 6
message = "Esto entre muchas comillas es un mensaje de largo 52".encode()
client_socketTCP.send(message)

# Cerrar conexión
print("Cerrando conexión")
client_socketTCP.close()
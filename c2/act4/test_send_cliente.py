import socket_tcp
import sys

if len(sys.argv) < 3:
    raise Exception("No se ha especificado una dirección")
elif len(sys.argv) < 4 or (sys.argv[3] != "True" and sys.argv[3] != "False"):
    raise Exception("No se ha indicado si se utilizará control de congestión o no.")

address = (sys.argv[1], int(sys.argv[2]))


# CLIENT
client_socketTCP = socket_tcp.SocketTCP()
client_socketTCP.connect(address)
client_socketTCP.set_congestion_control_on("True" == sys.argv[3])
# test 1
message = "Mensje de len=16".encode()
client_socketTCP.send(message, mode="go_back_n")
# test 2
message = "Mensaje de largo 19".encode()
client_socketTCP.send(message, mode="go_back_n")
# test 3
message = "Mensaje de largo 19".encode()
client_socketTCP.send(message, mode="go_back_n")
# test 4
message = "Mensaje de largo 19".encode()
client_socketTCP.send(message, mode="go_back_n")

# tests largos
print("Empiezan los tests largos")


# test 5
message = "Esto entre muchas comillas se supone que debe ser un mensaje de largo 72".encode()
client_socketTCP.send(message, mode="go_back_n")
# test 6
message = "Esto entre muchas comillas es un mensaje de largo 52".encode()
client_socketTCP.send(message, mode="go_back_n")

# test 7
# largo 120 carácteres
message = "El viejo faro sobre el acantilado rocoso guiaba pacientemente a los barcos perdidos durante aquella tormentosa noche.".encode()
client_socketTCP.send(message, mode="go_back_n")

# test 8
if len(sys.argv) < 5:
    print("No hay archivo para natie.txt para abrir. El test 8 se ignorará")
else:
    with open(sys.argv[4], "rb") as f:
        content = f.read()
        client_socketTCP.send(content, mode="go_back_n")    

# Cerrar conexión
print("Cerrando conexión")
client_socketTCP.close()
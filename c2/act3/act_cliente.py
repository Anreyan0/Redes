import socket
import pathlib
import socket_tcp

def split_message_16_bytes(file):
    path = input("Ingrese la ruta del archivo: ")
    with open(path, "rb") as f:
        content = f.read()
        splitted_content = [content[i:i*16] for i in range(0, len(content), 16)]


path = input("Ingrese la ruta del archivo: ")

print("Creando socket - cliente")

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

address = ("localhost", 5000)
client_socket.connect(address)

i = 0
file = []
dicc_client = dict()
seq = 0
with open(path, "rb") as f:
    content = f.read()
    file = [content[i:(i+16)] for i in range(0, len(content), 16)]

for j in range(len(file)):
    send_message = file[j]
    dicc_client["N-Secuencia"] = seq
    dicc_client["ACK"] = 1
    dicc_client["SYN"] = 0
    dicc_client["FIN"] = 0
    dicc_client["Mensaje"] = send_message
    sequence = socket_tcp.SocketTCP.create_segment(dicc_client)
    seq += 1
    client_socket.sendto(sequence, address)

print("Mensaje enviado")

buffer_size = 23
message, address = client_socket.recvfrom(buffer_size)

decoded_message = message.decode()

print(f"Respuesta del servidor {decoded_message}")

client_socket.close()



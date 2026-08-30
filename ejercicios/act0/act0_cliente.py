import socket

print("Creando socket - cliente")

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

address = ("localhost", 5000)
client_socket.connect(address)

message = "Hola, este es un mensaje de prueba"
end_of_message = "\n"

send_message = (message + end_of_message).encode()

print(f"Mandando el mensaje {send_message.decode()}")
client_socket.sendto(send_message, address)

print("Mensaje enviado")

buffer_size = 1024
message, address = client_socket.recvfrom(buffer_size)

decoded_message = message.decode()

print(f"Respuesta del servidor {decoded_message}")

client_socket.close()


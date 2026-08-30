import socket

def recieve_full_message(connection_socket, buff_size, end_sequence):
    recv_message, address = connection_socket.recvfrom(buff_size)
    full_message = recv_message

    is_end_of_message = contains_end_of_message(full_message.decode(), end_sequence)

    while not is_end_of_message:
        recv_message, address = connection_socket.recvfrom(buff_size)

        full_message += recv_message

        is_end_of_message = contains_end_of_message(full_message.decode(), end_sequence)

    return full_message, address

def contains_end_of_message(message, end_sequence):
    return message.endswith(end_sequence)

def remove_end_of_message(full_message, end_sequence):
    index = full_message.rfind(end_sequence)
    return full_message[:index]

if __name__ == "__main__":
    buff_size = 1024
    end_of_message = "\n"
    new_socket_address = ("localhost", 5000)

    print("Creando socket - servidor")

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    server_socket.bind(new_socket_address)

    print("Esperando clientes")

    while True:
        recv_message, address = server_socket.recvfrom(buff_size)

        print(f"Se ha recibido con éxito el mensaje {recv_message}")

        response_message = f"Se ha recibido con éxito el mensaje {recv_message}"

        server_socket.sendto(response_message.encode(), address)


import sys
import socket


if __name__ == "__main__":

    if len(sys.argv) < 3:
        raise Exception("No se ha especificado una dirección y puerto")
    elif len(sys.argv) < 4:
        raise Exception("No se ha especificado una tabla de rutas")

    ip = sys.argv[1]
    puerto = int(sys.argv[2])
    with open(sys.argv[3], "rb") as f:
            rutas = f.read()
    address = (ip, puerto)
    buff_size = 2048

    router_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    router_socket.bind(address)

    print(f"ip: {ip}; puerto: {puerto}; rutas: {rutas.decode()}")
    print("Esperando clientes\n")
    
    while True:
        recv_message, address = router_socket.recvfrom(buff_size)

        print(f"Se ha recibido un mensaje: {recv_message}\n")

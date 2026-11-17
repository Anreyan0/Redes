
import socket
import router
import sys
import random

if __name__ == "__main__":
    # nombre ip_final puerto_final msg ip_envio puerto_envio ttl
    if len(sys.argv) < 7:
        print("No hay suficientes argumentos")
    buff_size = 2048

    final_ip = sys.argv[1]
    final_puerto = int(sys.argv[2])
    final_address = (final_ip, final_puerto)
    message = sys.argv[3].encode()
    send_address = (sys.argv[4], int(sys.argv[5]))
    ttl = int(sys.argv[6])
    id = random.randint(0, 255)
    offset = 0
    tamaño = len(message)
    flag = 0

    ip_packet = socket.inet_aton(final_ip) + final_puerto.to_bytes(2) + ttl.to_bytes(1) + id.to_bytes(1) + offset.to_bytes(4) + tamaño.to_bytes(4) + flag.to_bytes(1) + message

    print("Creando socket - Script")

    script_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    script_socket.sendto(ip_packet, send_address)

    print(f"Paquete enviado: {router.parse_packet(ip_packet)}")

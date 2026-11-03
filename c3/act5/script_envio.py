
import socket
import router
import sys

if __name__ == "__main__":
    # nombre ip_final puerto_final msg ip_envio puerto_envio
    if len(sys.argv) < 6:
        print("No hay suficientes argumentos")
    buff_size = 2048

    final_ip = sys.argv[1]
    final_puerto = int(sys.argv[2])
    final_address = (final_ip, final_puerto)
    message = sys.argv[3].encode()
    send_address = (sys.argv[4], int(sys.argv[5]))
    
    ip_packet = socket.inet_aton(final_ip) + final_puerto.to_bytes(2) + message

    print("Creando socket - Script")

    script_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    script_socket.sendto(ip_packet, send_address)

    print(f"Paquete enviado: {router.parse_packet(ip_packet)}")

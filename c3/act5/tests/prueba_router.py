import sys
import os
import socket

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import router

if __name__ == "__main__":
    # nombre ip_final puerto_final msg ip_envio puerto_envio ttl
    if len(sys.argv) < 4:
        raise Exception("No hay suficientes argumentos")
    
    buff_size = 2048

    final_address_and_TTL = sys.argv[1].split(";")
    final_ip = final_address_and_TTL[0]
    final_port = int(final_address_and_TTL[1])
    TTL = int(final_address_and_TTL[2])

    send_address = (sys.argv[2], int(sys.argv[3]))
    script_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    with open("natie.txt", "r") as f:
        natie_text = f.read()
    
    lines = natie_text.split("\n")
    for message in lines:
        ip_packet = socket.inet_aton(final_ip) + final_port.to_bytes(2) + TTL.to_bytes(1) + message.encode()
        script_socket.sendto(ip_packet, send_address)
        
        print(f"Paquete enviado: {router.parse_packet(ip_packet)}") 

    script_socket.close()
           

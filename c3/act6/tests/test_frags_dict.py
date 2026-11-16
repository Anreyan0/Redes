# Test del item 7
# Manda dos paquetes IP de distinto ID, en fragmentos acorde al MTU del router R2
# Los manda desordenados, para testear el reensamble del router

import sys
import os
import socket
import random

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import router

ip_bytes = socket.inet_aton("127.0.0.1")
puerto = 8882
puerto_bytes = puerto.to_bytes(2)
TTL = 200
TTL_bytes = TTL.to_bytes(1)
ID = 67
ID_bytes = ID.to_bytes(1)
Offset = 0
Offset_bytes = Offset.to_bytes(4)
Tamaño = 200
Tamaño_bytes = Tamaño.to_bytes(4)
FLAG = 0
FLAG_bytes = FLAG.to_bytes(1)
mensaje = ("Nice Nature was born in 1988 at the Watanabe Ranch in Urakawa, Hokkaido. His sire, Nice Dancer, had six major wins in Canada, and his dam, Urakawa Miyuki, had three wins, including the 1984 open of wh").encode()
ip_packet_67 = ip_bytes + puerto_bytes + TTL_bytes + ID_bytes + Offset_bytes + Tamaño_bytes + FLAG_bytes + mensaje

ID_10 = 10
ID_10_bytes = ID_10.to_bytes(1)
mensaje_2 = ("According to the owner of the ranch Watanabe Kazuma. Nice Nature was average as a foal, nor did he stand out in the training ranch. However, Watanabe vaguely alluded that he felt that Nice Nature migh").encode()
ip_packet_10 = ip_bytes + puerto_bytes + TTL_bytes + ID_10_bytes + Offset_bytes + Tamaño_bytes + FLAG_bytes + mensaje_2

script_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

fragments_67 = router.fragment_IP_packet(ip_packet_67, 50)
fragments_10 = router.fragment_IP_packet(ip_packet_10, 50)
total_fragments = fragments_67 + fragments_10
random.shuffle(total_fragments)

for fragment in total_fragments:
    script_socket.sendto(fragment, ("127.0.0.1", 8882))
    print(f"Paquete de ID = {router.parse_packet(fragment)["ID"]} fue enviado a R2: {router.parse_packet(fragment)}")

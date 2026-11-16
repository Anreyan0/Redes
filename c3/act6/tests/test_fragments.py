# Test del item 5
# Prueba el funcionamiento de fragment_IP_packet y reassemble_IP_packet

import sys
import os
import socket
import random

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import router

ip_bytes = socket.inet_aton("127.0.0.1")
puerto = 8881
puerto_bytes = puerto.to_bytes(2)
TTL = 200
TTL_bytes = TTL.to_bytes(1)
ID = 67
ID_bytes = ID.to_bytes(1)
Offset = 0
Offset_bytes = Offset.to_bytes(4)
Tamaño = 100
Tamaño_bytes = Tamaño.to_bytes(4)
FLAG = 0
FLAG_bytes = FLAG.to_bytes(1)
mensaje = ("Nice Nature was born in 1988 at the Watanabe Ranch in Urakawa, Hokkaido. His sire, Nice Dancer, had ").encode()
packet_in_bytes_with_more_headers= ip_bytes + puerto_bytes + TTL_bytes + ID_bytes + Offset_bytes + Tamaño_bytes + FLAG_bytes + mensaje

MTU = 30
IP_packet_v1 = packet_in_bytes_with_more_headers
fragment_list = router.fragment_IP_packet(IP_packet_v1, MTU)
random.shuffle(fragment_list) # randomiza la lista de fragmentos para testear más a profundidad

IP_packet_v2 = router.reassemble_IP_packet(fragment_list)
print("IP_packet_v1 = IP_packet_v2 ? {}".format(IP_packet_v1 == IP_packet_v2))
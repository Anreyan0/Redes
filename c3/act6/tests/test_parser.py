import sys
import os
import socket

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import router

ip_bytes = socket.inet_aton("127.0.0.1")
puerto = 8881
puerto_bytes = puerto.to_bytes(2)
TTL = 200
TTL_bytes = TTL.to_bytes(1)
ID = 67
ID_bytes = ID.to_bytes(1)
Offset = 80
Offset_bytes = Offset.to_bytes(4)
Tamaño = 200
Tamaño_bytes = Tamaño.to_bytes(4)
FLAG = 0
FLAG_bytes = FLAG.to_bytes(1)
mensaje = b"holaamigos"
packet_in_bytes_with_more_headers= ip_bytes + puerto_bytes + TTL_bytes + ID_bytes + Offset_bytes + Tamaño_bytes + FLAG_bytes + mensaje

IP_packet_v1 = packet_in_bytes_with_more_headers #esto lo deben crear de forma manual de acuerdo a la estructura que hayan definido
parsed_IP_packet = router.parse_packet(IP_packet_v1)
IP_packet_v2 = router.create_packet(parsed_IP_packet)
print("IP_packet_v1 == IP_packet_v2 ? {}".format(IP_packet_v1 == IP_packet_v2))
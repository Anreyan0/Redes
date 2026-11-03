import sys
import os
import socket

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import router

ip_bytes = socket.inet_aton("127.0.0.1")
puerto = 8881
puerto_bytes = puerto.to_bytes(2)
mensaje = b"holaamigos"
packet_in_bytes = ip_bytes + puerto_bytes + mensaje

IP_packet_v1 = packet_in_bytes #esto lo deben crear de forma manual de acuerdo a la estructura que hayan definido
parsed_IP_packet = router.parse_packet(IP_packet_v1)
IP_packet_v2 = router.create_packet(parsed_IP_packet)
print("IP_packet_v1 == IP_packet_v2 ? {}".format(IP_packet_v1 == IP_packet_v2))
import socket
import random

class SocketTCP:
    def __init__(self):
        self.socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Tupla -> (ip, puerto)
        self.direccion_destino = ("", 0)
        self.direccion_origen = ("", 0)
        self.numero_secuencia = 0
        self.last_asf = 0
        self.buffer_parseado = []
    # int(4 bytes) 00000ASF = 5 bytes

    @staticmethod
    def parse_segment(segmento):
        dicc_parseo = dict()
        dicc_parseo["N-Secuencia"] = int.from_bytes(segmento[:4], byteorder='big')
        dicc_parseo["ACK"] = segmento.decode("utf-8")[4]
        dicc_parseo["SYN"] = segmento.decode("utf-8")[5]
        dicc_parseo["FIN"] = segmento.decode("utf-8")[6:7]
        dicc_parseo["Mensaje"] = segmento.decode("utf-8")[7:]
        return dicc_parseo
        
    @staticmethod
    def create_segment(parsed):
        sec = 1 + parsed["N-Secuencia"]
        sec = sec.to_bytes(4, byteorder='big')
        headers = (str(parsed["ACK"]) + str(parsed["SYN"]) + str(parsed["FIN"])).encode()
        mensaje = parsed["Mensaje"]
        return sec + headers + mensaje

    def bind(self, address):
        self.direccion_origen = address
        print("bind con éxito")
        return self.socket_udp.bind(address)

    # El connect es el cliente
    def connect(self, address):
        if self.direccion_origen == ("", 0):
            Exception("Se necesita un bind antes")

        self.direccion_destino = address

        sec = random.randint(0, 100)
        msg = sec.to_bytes(4) + bytes([0, 1, 0])

        self.socket_udp.sendto(msg, address)
        msg_2, new_address = self.socket_udp.recvfrom(7)
        msg_2 = self.parse_segment(msg_2)
        sec += 1
        
        if not(msg_2["N-Secuencia"] == sec + 1 and
               msg_2["ACK"] == "1" and
               msg_2["SYN"] == "1" and
               msg_2["FIN"] == "0"):
            ... #timeout

        msg = sec.to_bytes(4) + bytes([1, 0, 0])
        self.numero_secuencia = sec
        self.socket_udp.sendto(msg, new_address)

        print("connect con éxito")

    # El accept es el server
    def accept(self):
        if self.direccion_origen == ("", 0):
            Exception("Se necesita un bind antes")
        
        msg, address = self.socket_udp.recvfrom(7)
        msg_rcv = self.parse_segment(msg)
        sec = msg_rcv["N-Secuencia"] + 1

        if not (msg_rcv["ACK"] == "0" and
                msg_rcv["SYN"] == "1" and
                msg_rcv["FIN"] == "0"):
            ...

        msg_send = sec.to_bytes(4, byteorder='big') + bytes([1, 1, 0])
        new_socket = SocketTCP()
        new_socket.bind((self.direccion_origen[0], 0))
        #new_socket.direccion_destino = address
        new_socket.socket_udp.sendto(msg_send, address)

        msg_2, _ = new_socket.socket_udp.recvfrom(7)
        msg_2 = self.parse_segment(msg_2)
        if not (msg_2["ACK"] == "1" and
                msg_2["SYN"] == "0" and
                msg_2["FIN"] == "0"):
                    ...

        new_socket.numero_secuencia = msg_2["N-Secuencia"] + 1
        #crear socket y retornar uno nuevo
        print("accept con éxito")
        return new_socket, new_socket.direccion_origen
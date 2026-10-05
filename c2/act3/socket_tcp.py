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
        self.datos_sin_recibir = 0
        self.message_received = 0
    # int(4 bytes) A S F = 7 bytes

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
        self.direccion_destino = new_address

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
        new_socket.direccion_destino = address
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

    def send(self, msg):
        length = len(msg)
        first_msg = length.to_bytes(4, byteorder="big")
        mensaje_partido = [first_msg] + [msg[i:(i+16)] for i in range(0, length, 16)]
        i = 0
        while i < len(mensaje_partido):
            try:
                msg_send = self.numero_secuencia.to_bytes(4, byteorder="big") + bytes([1, 0, 0]) + mensaje_partido[i]

                self.socket_udp.sendto(msg_send, self.direccion_destino)
                self.socket_udp.settimeout(1)
                msg_recv, _ = self.socket_udp.recvfrom(7)
                msg_recv = self.parse_segment(msg_recv)

                if (msg_recv["ACK"] == "1" and
                    msg_recv["SYN"] == "0" and
                    msg_recv["FIN"] == "0"):
                    self.numero_secuencia = msg_recv["N-Secuencia"]
                    i += 1
                    continue
            except:
                pass


    def recv(self, buff_size):
        if self.datos_sin_recibir == 0:
            first, _ = self.socket_udp.recvfrom(11)
            first_msg = self.parse_segment(first)
            message_length = int.from_bytes(first_msg["Mensaje"].encode('latin-1'), byteorder='big')
            self.numero_secuencia = int(first_msg["N-Secuencia"])

            if message_length > buff_size:
                self.datos_sin_recibir = message_length
                return self.recv(buff_size)
            else:
                nuevo_mensaje = self.numero_secuencia.to_bytes(4, byteorder="big") + bytes([1, 0, 0])
                self.socket_udp.sendto(nuevo_mensaje, self.direccion_destino)

                received = 0
                message = b""
                while received != message_length:
                    msg, _ = self.socket_udp.recvfrom(7 + 16)
                    ack_msg = self.numero_secuencia.to_bytes(4, byteorder="big") + bytes([1, 0, 0])
                    received += len(self.parse_segment(msg)["Mensaje"])
                    self.socket_udp.sendto(ack_msg, self.direccion_destino)
                    message += self.parse_segment(msg)["Mensaje"].encode()
                
                return message

        else:
            real_message = b""

            if self.pending_bytes_recvfrm:
                self.last_message_position += buff_size

                
                msg, _  = self.socket_udp.recvfrom(7 + 16)
                parsed_msg = self.parse_segment(msg)
                real_message += parsed_msg["Mensaje"][self.last_message_position : (buff_size + self.last_message_position)].encode()

                self.pending_bytes_recvfrm -= len(real_message.decode())
                self.received_len += len(real_message.decode())

                if self.pending_bytes_recvfrm > buff_size:
                    return real_message
                else:
                    return real_message + self.recv(buff_size)         

            else:

                self.numero_secuencia += self.received_len
                ack_msg = self.numero_secuencia.to_bytes(4, byteorder="big") + bytes([1, 0, 0])
                self.socket_udp.sendto(ack_msg, self.direccion_destino)
                self.last_message_position = 0
                self.received_len = 0

                bytes_received = 0
                cycles = 0
                while bytes_received < buff_size:
                    if (bytes_received > 0):
                        self.numero_secuencia += 16
                        ack_msg = self.numero_secuencia.to_bytes(4, byteorder="big") + bytes([1, 0, 0])
                        self.socket_udp.sendto(ack_msg, self.direccion_destino)

                    msg, _  = self.socket_udp.recvfrom(7 + 16)
                    parsed_msg = self.parse_segment(msg)
                    if (parsed_msg["N-Secuencia"] != self.numero_secuencia):
                        ack_msg = self.numero_secuencia.to_bytes(4, byteorder="big") + bytes([1, 0, 0])
                        self.socket_udp.sendto(ack_msg, self.direccion_destino)

                    real_message += parsed_msg["Mensaje"][ : buff_size].encode()
                    bytes_received += 16
                    cycles += 1

                self.pending_bytes_recvfrm = (bytes_received - buff_size) if (len(real_message.decode()) == cycles*buff_size ) else 0
                self.received_len += buff_size

                if self.pending_bytes_recvfrm == 0:
                    self.numero_secuencia += len(real_message.decode())
                    ack_msg = self.numero_secuencia.to_bytes(4, byteorder="big") + bytes([1, 0, 0])
                    self.socket_udp.sendto(ack_msg, self.direccion_destino)

                return real_message
                

    # Administra el cierre de la conexión desde el Host A
    def close(self):
        first_msg = self.numero_secuencia.to_bytes(4, byteorder="big") + bytes([0, 0, 1])
        self.socket_udp.sendto(first_msg, self.direccion_destino)
        self.socket_udp.settimeout(1)

        response, _ = self.socket_udp.recvfrom(7)
        parsed_rsp = self.parse_segment(response)
        if (parsed_rsp["N-Secuencia"] == (self.numero_secuencia + 1) and
            parsed_rsp["ACK"] == "1" and
            parsed_rsp["SYN"] == "0" and
            parsed_rsp["FIN"] == "1"):

            self.numero_secuencia = parsed_rsp["N-Secuencia"] + 1
            final_msg = self.numero_secuencia.to_bytes(4, byteorder="big") + bytes([1, 0, 0])
            self.socket_udp.sendto(final_msg, self.direccion_destino)

            self.socket_udp.close()

    # Administra el cierre de la conexión desde el Host B
    def recv_close(self):
        first_msg, _ = self.socket_udp.recvfrom(7)
        parsed_msg = self.parse_segment(first_msg)

        if (parsed_msg["ACK"] == "0" and
            parsed_msg["SYN"] == "0" and
            parsed_msg["FIN"] == "1"):

            self.numero_secuencia = parsed_msg["N-Secuencia"] + 1
            second_msg = self.numero_secuencia.to_bytes(4, byteorder="big") + bytes([1, 0, 1])
            self.socket_udp.sendto(second_msg, self.direccion_destino)

            final_msg, _ = self.socket_udp.recvfrom(7)
            parsed_final = self.parse_segment(final_msg)
            if (parsed_final["N-Secuencia"] == (self.numero_secuencia + 1) and
                parsed_final["ACK"] == "1" and
                parsed_final["SYN"] == "0" and
                parsed_final["FIN"] == "0"):

                self.socket_udp.close()
    
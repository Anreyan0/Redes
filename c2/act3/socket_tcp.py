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
        self.cuerpo_msg = b'0'
        self.datos_sin_recibir = 0
        self.pending_bytes_recvfrm = 0
        self.received_len = 0
    # int(4 bytes) A S F = 7 bytes

    @staticmethod
    def parse_segment(segmento):
        dicc_parseo = dict()
        dicc_parseo["N-Secuencia"] = int.from_bytes(segmento[:4], byteorder='big')
        dicc_parseo["ACK"] = segmento[4]
        dicc_parseo["SYN"] = segmento[5]
        dicc_parseo["FIN"] = segmento[6]
        dicc_parseo["Mensaje"] = segmento[7:]
        return dicc_parseo
        
    @staticmethod
    def create_segment(parsed):
        sec = 1 + parsed["N-Secuencia"]
        sec = sec.to_bytes(4, byteorder='big')
        headers = bytes([parsed["ACK"], parsed["SYN"], parsed["FIN"]])
        mensaje = parsed["Mensaje"]
        return sec + headers + mensaje

    def bind(self, address):
        self.direccion_origen = address
        print("bind con éxito")
        return self.socket_udp.bind(address)

    # El connect es el cliente
    def connect(self, address):

        self.direccion_destino = address

        sec = random.randint(0, 100)
        #print(sec)
        self.numero_secuencia = sec
        msg = self.numero_secuencia.to_bytes(4) + bytes([0, 1, 0])
        
        while True:
            try:
                print("Enviando primer mensaje de connect (SYN)")
                self.socket_udp.sendto(msg, address)
                self.socket_udp.settimeout(1)
                print("Recibiendo mensaje...")
                msg_2, new_address = self.socket_udp.recvfrom(7)
                print("Mensaje recibido!")
                msg_2_parsed = self.parse_segment(msg_2)

                if (msg_2_parsed["N-Secuencia"] == self.numero_secuencia + 1 and
                    msg_2_parsed["ACK"] == 1 and
                    msg_2_parsed["SYN"] == 1 and
                    msg_2_parsed["FIN"] == 0):
                    print("Mensaje correcto")
                    break
                print(f"Mensaje incorrecto por header: {msg_2}")
                print(msg_2_parsed)
            except:
                print("Timeout")
        
        self.numero_secuencia = msg_2_parsed["N-Secuencia"] + 1
        msg = self.numero_secuencia.to_bytes(4) + bytes([1, 0, 0])
        print("Envío del segundo mensaje de connect (ACK)")
        self.socket_udp.sendto(msg, new_address)
        self.direccion_destino = new_address

        print("connect con éxito")

    # El accept es el server
    def accept(self):
        if self.direccion_origen == ("", 0):
            raise Exception("Se necesita un bind antes")
        
        self.socket_udp.settimeout(1)

        while True:
            try:
                print("Esperando a recibir un mensaje...")
                msg, address = self.socket_udp.recvfrom(7)
                print("Mensaje recibido!")
                msg_rcv = self.parse_segment(msg)
                if (msg_rcv["ACK"] == 0 and
                    msg_rcv["SYN"] == 1 and
                    msg_rcv["FIN"] == 0):
                    print("Header correcto")
                    sec = msg_rcv["N-Secuencia"]
                    break
                print(f"Header incorrecto: {msg}")
                print(msg_rcv)
            except:
                print("Timeout")

        self.numero_secuencia = sec + 1
        #print(self.numero_secuencia)
        msg_send = self.numero_secuencia.to_bytes(4, byteorder='big') + bytes([1, 1, 0])

        new_socket = SocketTCP()
        new_socket.bind((self.direccion_origen[0], 0))
        new_socket.direccion_origen = new_socket.socket_udp.getsockname()
        new_socket.numero_secuencia = self.numero_secuencia
        new_socket.direccion_destino = address

        new_socket.socket_udp.settimeout(1)
        while True:
            try:
                print("Enviando mensaje de respuesta (SYN + ACK)")
                new_socket.socket_udp.sendto(msg_send, address)

                print("Esperando mensaje de respuesta...")
                # En esta sección esperamos 21 bytes para cubrir el caso de que se pierda el ACK
                # y haya que asumirlo desde el siguiente mensaje introducido en stop and wait
                msg_2, _ = new_socket.socket_udp.recvfrom(7 + 16)
                print("Mensaje recibido")
                msg_2_parsed = self.parse_segment(msg_2)
                if (msg_2_parsed["N-Secuencia"] == new_socket.numero_secuencia + 1 and
                    msg_2_parsed["ACK"] == 1 and
                    msg_2_parsed["SYN"] == 0 and
                    msg_2_parsed["FIN"] == 0):
                    print("ACK recibido por parte del cliente")
                    break
                elif (msg_2_parsed["N-Secuencia"] == new_socket.numero_secuencia + 1 and
                      len(msg_2_parsed["Mensaje"]) > 0):
                    print("se perdió el ACK del cliente, pero está empezando a mandar su contenido")
                    self.numero_secuencia = msg_2_parsed["N-Secuencia"]
                    new_socket.cuerpo_msg = msg_2_parsed["Mensaje"]
                    break
                    
                else:
                    print("No se recibió un mensaje correcto. Ni ACK ni contenido")

            except:
                print("Timeout")
            
        new_socket.numero_secuencia = msg_2_parsed["N-Secuencia"]
        #crear socket y retornar uno nuevo
        print("accept con éxito")
        
        new_socket.socket_udp.settimeout(None)
        self.socket_udp.settimeout(None)
        return new_socket, new_socket.direccion_origen

    def send(self, msg):
        length = len(msg)
        first_msg = length.to_bytes(4, byteorder="big")
        mensaje_partido = [first_msg] + [msg[i:(i+16)] for i in range(0, length, 16)]
        i = 0
        while i < len(mensaje_partido):
            try:
                msg_send = self.numero_secuencia.to_bytes(4, byteorder="big") + bytes([0, 0, 0]) + mensaje_partido[i]
                print("Enviando mensaje")
                self.socket_udp.sendto(msg_send, self.direccion_destino)
                self.socket_udp.settimeout(1)
                print("Esperando respuesta...")
                msg_recv, _ = self.socket_udp.recvfrom(7)
                print("Respuesta recibida")
                msg_recv_parsed = self.parse_segment(msg_recv)

                if (msg_recv_parsed["ACK"] == 0 and
                    msg_recv_parsed["SYN"] == 0 and
                    msg_recv_parsed["FIN"] == 0 and
                    msg_recv_parsed["N-Secuencia"] == self.numero_secuencia + len(mensaje_partido[i])):
                    print("Header correcto")
                    self.numero_secuencia = msg_recv_parsed["N-Secuencia"]
                    i += 1
                    continue
                print(f"Header incorrecto: {msg_recv}")
                print(msg_recv_parsed)
            except:
                print("Timeout")


    def recv(self, buff_size):
        # Revisamos si ya llegó el largo del mensaje o n
        if self.cuerpo_msg > b'0':
            self.received_len = self.cuerpo_msg
            if buff_size < len(self.cuerpo_msg):
                recivied = self.cuerpo_msg[:buff_size]
                self.pending_bytes_recvfrm = self.cuerpo_msg[buff_size:]
            elif buff_size == len(self.cuerpo_msg):
                recivied = self.cuerpo_msg
            else:
                recivied = self.cuerpo_msg
        else:
            while True:
                try:
                    print("Esperando mensaje...")
                    msg, _ = self.socket_udp.recvfrom(23)
                    print("Mensaje recibido")
                    parsed_msg = self.parse_segment(msg)
                    if (len(parsed_msg["Mensaje"]) > 0 and                      # Debe de existir el mensaje
                        parsed_msg["N-Secuencia"] == self.numero_secuencia):    # En este caso el número de secuencia del primer mensaje y del ACK es el mismo
                        print("Header correcto")
                        self.received_len = parsed_msg["Mensaje"]
                        response = parsed_msg["N-Secuencia"].to_bytes() + bytes([0, 0, 0])
                        self.numero_secuencia = parsed_msg["N-Secuencia"] + self.received_len
                        self.socket_udp.sendto(response, self.direccion_destino)
                        break
                    print(f"Header incorrecto: {msg}")
                    print(parsed_msg)
                except:
                    print("Timeout")
        
        self.datos_sin_recibir = buff_size
        # Comenzamos a recibir los segmentos del mensaje send
        ret = ""
        while self.datos_sin_recibir > 0:
            try:
                print("Esperando mensaje...")
                msg_recv, _ = self.socket_udp.recvfrom(23)
                print("Mensaje recibido!")
                parsed_msg_recv = self.parse_segment(msg_recv)
                
                # Separamos los casos según el número de secuencia entregado y recibido
                # Esperábamos este mensaje
                if parsed_msg_recv["N-Secuencia"] == self.numero_secuencia:
                    len_msg = len(parsed_msg_recv["Mensaje"])
                    self.numero_secuencia = parsed_msg_recv["N-Secuencia"] + len_msg
                    self.datos_sin_recibir -= len_msg
                    if len_msg > buff_size:
                        self.cuerpo_msg = parsed_msg_recv["Mensaje"][buff_size:]
                    ret += parsed_msg_recv["Mensaje"].decode("utf-8")
                    resp = self.numero_secuencia.to_bytes() + bytes([0, 0, 0])
                    print("Enviando confirmación de mensaje")
                    self.socket_udp.sendto(resp, self.direccion_destino)
                # Este mensaje ya fue recibido
                elif parsed_msg_recv["N-Secuencia"] < self.numero_secuencia:
                    resp = parsed_msg_recv["N-Secuencia"].to_bytes() + len(parsed_msg_recv["Mensaje"]) + bytes([0, 0, 0])
                    print("Enviando confirmación repetida")
                    self.socket_udp.sendto(resp, self.direccion_destino)
                # El mensaje no era para nosotros
                else:
                    print("Header incorrecto")
            except:
                print("Timeout")

        return ret



                

    # Administra el cierre de la conexión desde el Host A
    def close(self):
        #print(self.numero_secuencia)
        self.numero_secuencia += 1
        first_msg = self.numero_secuencia.to_bytes(4, byteorder="big") + bytes([0, 0, 1])
        counter = 0
        self.socket_udp.settimeout(1)
        
        while counter < 3:
            try:
                print("Enviando primer mensaje de close")
                self.socket_udp.sendto(first_msg, self.direccion_destino)
                print("Esperando respuesta...")
                response, _ = self.socket_udp.recvfrom(7)
                print("Mensaje recibido!")
                parsed_rsp = self.parse_segment(response)
                    
                if (parsed_rsp["N-Secuencia"] == (self.numero_secuencia + 1) and
                    parsed_rsp["ACK"] == 1 and
                    parsed_rsp["SYN"] == 0 and
                    parsed_rsp["FIN"] == 1):
                    print("Header correcto!")
                    break
                
                print("Header incorrecto")
            except socket.timeout:
                print("Timeout")
                counter += 1
            except Exception as e:
                print(e)
            

        if parsed_rsp is not None:
            self.numero_secuencia = parsed_rsp["N-Secuencia"] + 1
            final_msg = self.numero_secuencia.to_bytes(4, byteorder="big") + bytes([1, 0, 0])
            self.socket_udp.sendto(final_msg, self.direccion_destino)

        self.socket_udp.close()

    # Administra el cierre de la conexión desde el Host B
    def recv_close(self):
        counter = 0
        fin = False
        #print(self.numero_secuencia)

        while counter < 3:
            try:
                print("Esperando mensajes...")
                self.socket_udp.settimeout(1)
                msg, _ = self.socket_udp.recvfrom(7)
                print("Mensaje recibido")
                parsed_msg = self.parse_segment(msg)

                if not fin:
                    if (parsed_msg["N-Secuencia"] == self.numero_secuencia + 1 and
                        parsed_msg["ACK"] == 0 and
                        parsed_msg["SYN"] == 0 and
                        parsed_msg["FIN"] == 1):
                        
                        print("Mensaje FIN recibido")
                        self.numero_secuencia = parsed_msg["N-Secuencia"] + 1
                        second_msg = self.numero_secuencia.to_bytes(4, byteorder="big") + bytes([1, 0, 1])
                        print("Enviando mensaje (FIN + ACK)")
                        self.socket_udp.sendto(second_msg, self.direccion_destino)
                        fin = True
                        counter = 0

                    else:
                        print(f"Header incorrecto 1: {msg}")
                        print(parsed_msg)
                        print(self.numero_secuencia)
                else:
                    if (parsed_msg["N-Secuencia"] == self.numero_secuencia + 1 and
                        parsed_msg["ACK"] == 1 and
                        parsed_msg["SYN"] == 0 and
                        parsed_msg["FIN"] == 0):
                        break
                    else:
                        print(f"Header incorrecto 2: {msg}")
                        print(parsed_msg)
                        print(self.numero_secuencia)

            except socket.timeout:
                print("Timeout")
                counter += 1
            except Exception as e:
                print(e)

        print("Cerrando socket")
        self.socket_udp.close()
    
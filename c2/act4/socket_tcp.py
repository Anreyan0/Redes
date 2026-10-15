import socket
import random
import socketUDP
import CongestionControl
import slidingWindowCC

class SocketTCP:
    def __init__(self):
        self.socket_udp = socketUDP.SocketUDP()
        # Tupla -> (ip, puerto)
        self.direccion_destino = ("", 0)
        self.direccion_origen = ("", 0)
        self.numero_secuencia = 0
        self.last_asf = 0
        self.cuerpo_msg = b''
        self.pending_bytes_recvfrm = b''
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
        self.socket_udp.settimeout(1)
        
        while True:
            try:
                print("Enviando primer mensaje de connect (SYN)")
                print(self.parse_segment(msg))
                self.socket_udp.sendto(msg, address)
                print("Recibiendo mensaje...")
                msg_2, new_address = self.socket_udp.recvfrom(7)
                print("Mensaje recibido!")
                msg_2_parsed = self.parse_segment(msg_2)

                if (msg_2_parsed["N-Secuencia"] == self.numero_secuencia + 1 and
                    msg_2_parsed["ACK"] == 1 and
                    msg_2_parsed["SYN"] == 1 and
                    msg_2_parsed["FIN"] == 0):
                    print("Mensaje correcto")
                    self.socket_udp.stop_timer()
                    break
                print(f"Mensaje incorrecto por header: {msg_2}")
                print(msg_2_parsed)
            except socket.timeout:
                print("Timeout")
            except Exception as e:
                print(e)
        
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
            except socket.timeout:
                print("Timeout")
            except Exception as e:
                print(e)

        self.numero_secuencia = sec + 1
        #print(self.numero_secuencia)
        msg_send = self.numero_secuencia.to_bytes(4, byteorder='big') + bytes([1, 1, 0])

        new_socket = SocketTCP()
        new_socket.bind((self.direccion_origen[0], 0))
        new_socket.direccion_origen = (self.direccion_origen[0], 0)
        new_socket.numero_secuencia = self.numero_secuencia
        new_socket.direccion_destino = address

        while True:
            try:
                print("Enviando mensaje de respuesta (SYN + ACK)")
                new_socket.socket_udp.sendto(msg_send, address)

                print("Esperando mensaje de respuesta...")
                # En esta sección esperamos 23 bytes para cubrir el caso de que se pierda el ACK
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

            except socket.timeout:
                print("Timeout")
            except Exception as e:
                print(e)

        new_socket.numero_secuencia = msg_2_parsed["N-Secuencia"]
        #crear socket y retornar uno nuevo
        print("accept con éxito")
        
        return new_socket, new_socket.direccion_origen

    def send(self, msg, mode="stop_and_wait"):
        if mode == "stop_and_wait":
            self.send_using_stop_and_wait(msg)
        elif mode == "go_back_n":
            self.send_using_go_back_n(msg)

    def send_using_stop_and_wait(self, msg):
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
                    self.socket_udp.stop_timer()
                    i += 1
                    continue
                print("Header incorrecto")
            except socket.timeout:
                print("Timeout")
            except Exception as e:
                print(e)

    def send_using_go_back_n(self, msg: bytes) -> None:
        message_length = len(msg).to_bytes(4, byteorder="big")
        # dividimos el mensaje en trozos de 16 bytes
        data_list = [msg[i:(i+16)] for i in range(0, len(msg), 16)]
        full_data_list = [message_length] + data_list
        full_length = len(full_data_list)

        # usamos una ventana para que vean como se usa
        initial_seq = self.numero_secuencia
        data_to_send = slidingWindowCC.SlidingWindowCC(8, full_data_list, initial_seq)
        wnd_index = 0
        print(data_to_send)

        # partimos armando y enviando el primer segmento
        current_data = data_to_send.get_data(0)
        current_seq = data_to_send.get_sequence_number(0)
        current_segment = current_seq.to_bytes(4, byteorder="big") + bytes([0, 0, 0]) + current_data

        first_sequence = True
        i = 1
        k = 0
        while current_data is not None:
            print(self.parse_segment(current_segment))
            self.numero_secuencia = current_seq
            self.socket_udp.sendto(current_segment, self.direccion_destino, timer_index=0)

            try:
                answer, address = self.socket_udp.recvfrom(7)
                parsed_answer = self.parse_segment(answer)
                print(f"recibido: {parsed_answer}\n")
                if (parsed_answer["ACK"] == 0 and
                    parsed_answer["SYN"] == 0 and
                    parsed_answer["FIN"] == 0 and
                    parsed_answer["N-Secuencia"] >= self.numero_secuencia):
                    self.socket_udp.stop_timer(timer_index=0)
                    k += 1

                    if first_sequence == True:
                        current_data = data_to_send.get_data(i)
                        if current_data is not None:
                            current_seq = data_to_send.get_sequence_number(i)
                            current_segment = current_seq.to_bytes(4, byteorder="big") + bytes([0, 0, 0]) + current_data
                            i += 1
                            if i == 7:
                                first_sequence = False
                        else:
                            self.numero_secuencia += len(self.parse_segment(current_segment)["Mensaje"]) 

                    else:
                        # movemos ventana
                        amount_of_moves = round(((parsed_answer["N-Secuencia"] - (self.numero_secuencia)) / 16) + 1)
                        data_to_send.move_window(amount_of_moves)

                        current_data = data_to_send.get_data(7)
                        if current_data is not None:
                            self.numero_secuencia = current_seq
                            current_seq = data_to_send.get_sequence_number(7)
                            current_segment = current_seq.to_bytes(4, byteorder="big") + bytes([0, 0, 0]) + current_data

            except TimeoutError:
                for l in range(0,8):
                    current_data = data_to_send.get_data(l)
                    if current_data is not None:
                        current_seq = data_to_send.get_sequence_number(l)
                        current_segment = current_seq.to_bytes(4, byteorder="big") + bytes([0, 0, 0]) + current_data
                        self.socket_udp.sendto(current_segment, self.direccion_destino, timer_index=0)
                    else:
                        break
                print("Timeout")



    def recv(self, buff_size, mode="stop_and_wait"):
        if mode == "stop_and_wait":
            return self.recv_using_stop_and_wait(buff_size)
        elif mode == "go_back_n":
            return self.recv_using_go_back_n(buff_size)

                
    def recv_using_stop_and_wait(self, buff_size):
        # Revisamos si ya llegó el largo del mensaje o n
        # Notar que el recv del leargo total del mensaje va por detrás y no está considerado como mensaje para ser entregado
        # Asumiremos que el alrgo del mensaje que se desea enviar lograr entrar en 16 bytes
        print(self.received_len)
        if self.received_len == 0:
            print("revisando bytes de largo del mensaje")
            if self.cuerpo_msg != b'':
                print("El largo llegó en el accept")
                self.received_len = int.from_bytes(self.cuerpo_msg)
                self.numero_secuencia += len(self.cuerpo_msg)
                response = self.numero_secuencia.to_bytes(4) + bytes([0, 0, 0])
                self.cuerpo_msg = b''
                self.socket_udp.sendto(response, self.direccion_destino)
            else:
                print("recibiendo el largo del mensaje")
                while True:
                    try:
                        print("Esperando mensaje...")
                        msg, _ = self.socket_udp.recvfrom(23)
                        print("Mensaje recibido")
                        parsed_msg = self.parse_segment(msg)
                        if (len(parsed_msg["Mensaje"]) > 0 and                      # Debe de existir el mensaje
                            parsed_msg["N-Secuencia"] == self.numero_secuencia):    # En este caso el número de secuencia del primer mensaje y del ACK es el mismo
                            print("Header correcto")
                            self.received_len = int.from_bytes(parsed_msg["Mensaje"])
                            self.numero_secuencia += len(parsed_msg["Mensaje"])
                            response = self.numero_secuencia.to_bytes(4) + bytes([0, 0, 0])
                            self.socket_udp.sendto(response, self.direccion_destino)
                            break
                        print("Header incorrecto")
                    except socket.timeout:
                        print("Timeout")
                    except Exception as e:
                        print(e)

        cant_min = min(self.received_len, buff_size)

        # En el caso de que hayan suficientes bytes recibidos por el buffer fijo interno
        # No esperamos más respuestas si no que solo entregamos lo que hemos conservado aún
        if len(self.pending_bytes_recvfrm) >= cant_min:
            ret = self.pending_bytes_recvfrm[:cant_min]
            self.pending_bytes_recvfrm = self.pending_bytes_recvfrm[cant_min:]
            self.received_len -= len(ret)
            return ret
        

        self.datos_sin_recibir = cant_min
        # Comenzamos a recibir los segmentos del mensaje send
        ret = b""
        while len(ret) < cant_min:
            try:
                print("Esperando mensaje...")
                msg_recv, _ = self.socket_udp.recvfrom(23)
                print("Mensaje recibido!")
                parsed_msg_recv = self.parse_segment(msg_recv)
                
                # Separamos los casos según el número de secuencia entregado y recibido
                # Esperábamos este mensaje
                if parsed_msg_recv["N-Secuencia"] == self.numero_secuencia:
                    print("Mensaje esperado")
                    self.pending_bytes_recvfrm += parsed_msg_recv["Mensaje"]
                    if len(self.pending_bytes_recvfrm) >= cant_min:
                        ret_iteration = self.pending_bytes_recvfrm[:cant_min]
                        self.pending_bytes_recvfrm = self.pending_bytes_recvfrm[cant_min:]
                    else:
                        ret_iteration = self.pending_bytes_recvfrm
                        self.pending_bytes_recvfrm = b''
                    ret += ret_iteration
                    self.numero_secuencia += len(parsed_msg_recv["Mensaje"])
                    self.datos_sin_recibir -= len(ret_iteration)
                    resp = self.numero_secuencia.to_bytes(4) + bytes([0, 0, 0])
                    print("Enviando confirmación de mensaje")
                    self.socket_udp.sendto(resp, self.direccion_destino)
                # Este mensaje ya fue recibido
                elif parsed_msg_recv["N-Secuencia"] < self.numero_secuencia:
                    print("Mensaje repetido")
                    secuencia = parsed_msg_recv["N-Secuencia"] + len(parsed_msg_recv["Mensaje"])
                    resp = secuencia.to_bytes(4) + bytes([0, 0, 0])
                    print("Enviando confirmación repetida")
                    self.socket_udp.sendto(resp, self.direccion_destino)
                # El mensaje no era para nosotros
                else:
                    print("Header incorrecto")
            except socket.timeout:
                print("Timeout")
            except Exception as e:
                print(e)

        self.received_len -= len(ret)
        return ret

    def recv_using_go_back_n(self, buff_size):
        # Revisamos si ya llegó el largo del mensaje o n
        # Notar que el recv del largo total del mensaje va por detrás y no está considerado como mensaje para ser entregado
        # Asumiremos que el alrgo del mensaje que se desea enviar lograr entrar en 16 bytes
        print(self.received_len)
        if self.received_len == 0:
            print("Revisando bytes de largo del mensaje")
            if self.cuerpo_msg != b'':
                print("El largo llegó en el accept")
                self.received_len = int.from_bytes(self.cuerpo_msg)
                self.numero_secuencia += len(self.cuerpo_msg)
                response = self.numero_secuencia.to_bytes(4) + bytes([0, 0, 0])
                self.cuerpo_msg = b''
                self.socket_udp.sendto(response, self.direccion_destino)
            else:
                print("Recibiendo el largo del mensaje")
                while True:
                    try:
                        print("Esperando mensaje...")
                        msg, _ = self.socket_udp.recvfrom(23)
                        print("Mensaje recibido")
                        parsed_msg = self.parse_segment(msg)
                        if (len(parsed_msg["Mensaje"]) > 0 and                      # Debe de existir el mensaje
                            parsed_msg["N-Secuencia"] == self.numero_secuencia):    # En este caso el número de secuencia del primer mensaje y del ACK es el mismo
                            print("Header correcto")
                            self.received_len = int.from_bytes(parsed_msg["Mensaje"])
                            self.numero_secuencia += len(parsed_msg["Mensaje"])
                            response = parsed_msg["N-Secuencia"].to_bytes(4) + bytes([0, 0, 0])
                            self.socket_udp.sendto(response, self.direccion_destino)
                            break
                        print("Header incorrecto")
                    except socket.timeout:
                        print("Timeout")
                    except Exception as e:
                        print(e)
        
        cant_min = min(self.received_len, buff_size)

        # En el caso de que hayan suficientes bytes recibidos por el buffer fijo interno
        # No esperamos más respuestas si no que solo entregamos lo que hemos conservado aún
        if len(self.pending_bytes_recvfrm) >= cant_min:
            ret = self.pending_bytes_recvfrm[:cant_min]
            self.pending_bytes_recvfrm = self.pending_bytes_recvfrm[cant_min:]
            self.received_len -= len(ret)
            return ret
        

        self.datos_sin_recibir = cant_min
        # Comenzamos a recibir los segmentos del mensaje send
        ret = b""
        while len(ret) < cant_min:
            try:
                print("Esperando mensaje...")
                msg_recv, _ = self.socket_udp.recvfrom(23)
                print("Mensaje recibido!")
                parsed_msg_recv = self.parse_segment(msg_recv)
                
                # Separamos los casos según el número de secuencia entregado y recibido
                # Esperábamos este mensaje
                if parsed_msg_recv["N-Secuencia"] == self.numero_secuencia:
                    print("Mensaje esperado")
                    self.pending_bytes_recvfrm += parsed_msg_recv["Mensaje"]
                    if len(self.pending_bytes_recvfrm) >= cant_min:
                        ret_iteration = self.pending_bytes_recvfrm[:cant_min]
                        self.pending_bytes_recvfrm = self.pending_bytes_recvfrm[cant_min:]
                    else:
                        ret_iteration = self.pending_bytes_recvfrm
                        self.pending_bytes_recvfrm = b''
                    ret += ret_iteration
                    self.numero_secuencia += len(parsed_msg_recv["Mensaje"])
                    self.datos_sin_recibir -= len(ret_iteration)
                    resp = (self.numero_secuencia - len(parsed_msg_recv["Mensaje"])).to_bytes(4) + bytes([0, 0, 0])
                    print("Enviando confirmación de mensaje")
                    self.socket_udp.sendto(resp, self.direccion_destino)
                # Este mensaje ya fue recibido
                elif parsed_msg_recv["N-Secuencia"] < self.numero_secuencia:
                    print("Mensaje repetido")
                    secuencia = parsed_msg_recv["N-Secuencia"] + len(parsed_msg_recv["Mensaje"])
                    resp = secuencia.to_bytes(4) + bytes([0, 0, 0])
                    print("Enviando confirmación repetida")
                    self.socket_udp.sendto(resp, self.direccion_destino)
                # El mensaje no era para nosotros
                else:
                    print("Header incorrecto")
            except socket.timeout:
                print("Timeout")
            except Exception as e:
                print(e)
                
        self.received_len -= len(ret)
        return ret

    # Administra el cierre de la conexión desde el Host A
    def close(self):
        #print(self.numero_secuencia)
        self.numero_secuencia += 1
        first_msg = self.numero_secuencia.to_bytes(4, byteorder="big") + bytes([0, 0, 1])
        counter = 0
        self.socket_udp.settimeout(1)
        parsed_rsp = None

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
        print("Cerrando conexión")
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
                        print("Header incorrecto 1")
                else:
                    if (parsed_msg["N-Secuencia"] == self.numero_secuencia + 1 and
                        parsed_msg["ACK"] == 1 and
                        parsed_msg["SYN"] == 0 and
                        parsed_msg["FIN"] == 0):
                        break
                    else:
                        print("Header incorrecto 2")

            except socket.timeout:
                print("Timeout")
                counter += 1
            except Exception as e:
                print(e)

        print("Cerrando socket")
        self.socket_udp.close()
    
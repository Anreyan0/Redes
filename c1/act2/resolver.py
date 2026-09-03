import binascii
import socket


def send_dns_message(address, port):
    # Encabezado con ID 0 (00 00 en hexadecimal), preguntamos por example.com
    header = "00 00 00 00 00 01 00 00 00 00 00 00 ".replace(" ","")
    data = "07 65 78 61 6D 70 6C 65 03 63 6F 6D 00 00 01 00 01".replace(" ","")
    message = header + data
    # Lo escribimos así para que se entendiera, lo concatenamos para hacer la cadena de hexadecimales
    server_address = (address, port)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # usamos binascii para pasar el mensaje al formato apropiado
        binascii_msg = binascii.unhexlify(message)
        # y lo enviamos
        sock.sendto(binascii_msg, server_address)
        # En data quedará la respuesta a nuestra consulta
        data, _ = sock.recvfrom(4096)
    finally:
        sock.close()
    
    return binascii.hexlify(data).decode("utf-8")

def get_name(msg, offset):
    name = []
    while msg[offset: offset +2] != "00":
        if int(msg[offset: offset + 2], 16) >= int("C0", 16):
            # Si el primer byte es 11, significa que es un puntero
            # Hacemos una mascara del offset con 0x3FFF que es 0011 1111 1111 1111 en binario
            name.append(get_name(msg, (int(msg[offset:offset + 4], 16) & 0x3FFF) * 2)[0])
            return ".".join(name), offset + 4
        # Extraemos el largo
        largo = int(msg[offset:offset + 2], 16)
        # Extraemos el dominio y lo enviamos a la lista del dominio para su construccion
        name.append(bytes.fromhex(msg[offset + 2:offset + 2 + largo * 2]).decode("utf-8"))
        # Actualizamos el offset para continuar leyendo
        offset += largo * 2 + 2
    return ".".join(name), offset + 2

def get_rr(msg, offset, count):
    rr_list = []
    # Iteramos por cada rr que se indique 11xx
    for i in range(count):
        rr = []
        # La estructura de la sección Answer es la siguiente
        if int(msg[offset: offset + 2], 16) >= int("C0", 16):
            # Si el primer byte es 11, significa que es un puntero
            # Hacemos una mascara del offset con 0x3FFF que es 0011 1111 1111 1111 en binario
            dominio, _ = get_name(msg, (int(msg[offset:offset + 4], 16) & 0x3FFF) * 2)
            rr.append(dominio)                                          # name
            offset += 4
        else:
            # En el caso de que no sea un puntero leemos el nombre completo
            dominio, offset = get_name(msg, offset)
            rr.append(dominio)                                          # name

        rr.append(int(msg[offset:offset + 4], 16))                      # type
        rr.append(int(msg[offset + 4:offset + 8], 16))                  # class
        rr.append(int(msg[offset + 8:offset + 16], 16))                 # ttl
        rr.append(int(msg[offset + 16:offset + 20], 16))                # rdlength
        if rr[1] == 1 or rr[1] == 28: # TYPE: A o AAAA                    rddata
            rr.append(get_ip(rr[1], int(msg[offset + 20:offset + 20 + rr[-1] * 2], 16)))
        elif rr[1] == 2 or rr[1] == 5: # TYPE: NS o CNAME
            if int(msg[offset + 20: offset + 22], 16) >= int("C0", 16):
                rr.append(get_name(msg, int(msg[offset + 20:offset + 24], 16) & 0x3FFF)[0])
            else:
                rr.append(get_name(msg, offset + 20)[0])
        else:
            if rr[4] != 0:
                rr.append(int(msg[offset + 20: offset + 20 + (2 * rr[4])], 16))
            else:
                rr.append(0)

        rr_list.append(rr)
        # Actualizamos el offset según lo recorrido y lo que indique rdlength para seguir iterando
        offset += 20 + rr[-2] * 2

    return rr_list, offset

def pars_msg(msg):
    parser = dict()
    # Header    
    headers = ["ID", "Campos", "QDCOUNT", "ANCOUNT", "NSCOUNT", "ARCOUNT"]
    for i in range(len(headers)):
        parser[headers[i]] = int(msg[i * 4:(i + 1) * 4], 16)
    # Question
    offset = 24

    if parser["QDCOUNT"] > 0:
        # Iteramos por cada pregunta que haya
        for nQuestion in range(parser["QDCOUNT"]):
            dominio, offset = get_name(msg, offset)

            # Construimos cada elemento de la secciónd de Question
            parser[f"QNAME{nQuestion}"] = dominio
            parser[f"QTYPE{nQuestion}"] = int(msg[offset:offset + 4], 16)
            parser[f"QCLASS{nQuestion}"] = int(msg[offset + 4:offset + 8], 16)
            offset += 8

    if parser["ANCOUNT"] > 0:
        # obtenemos lista de respuestas como rr's
        rr, offset = get_rr(msg, offset, parser["ANCOUNT"])
        # Iteramos por respuesta que haya (entregado como rr's)
        for nAnswer in range(parser["ANCOUNT"]):
            parser[f"ANSWERNAME{nAnswer}"] = rr[nAnswer][0]
            parser[f"ANSWERTYPE{nAnswer}"] = rr[nAnswer][1]
            parser[f"ANSWERCLASS{nAnswer}"] = rr[nAnswer][2]
            parser[f"ANSWERTTL{nAnswer}"] = rr[nAnswer][3]
            parser[f"ANSWERRDLENGTH{nAnswer}"] = rr[nAnswer][4]
            parser[f"ANSWERRDDATA{nAnswer}"] = rr[nAnswer][5]

    if parser["NSCOUNT"] > 0:
        auth, offset = get_rr(msg, offset, parser["NSCOUNT"])
        for nAuth in range(parser["NSCOUNT"]):
            parser[f"AUTHORITYNAME{nAuth}"] = auth[nAuth][0] 
            parser[f"AUTHORITYTYPE{nAuth}"] = auth[nAuth][1] 
            parser[f"AUTHORITYCLASS{nAuth}"] = auth[nAuth][2] 
            parser[f"AUTHORITYTTL{nAuth}"] = auth[nAuth][3] 
            parser[f"AUTHORITYRDLENGTH{nAuth}"] = auth[nAuth][4] 
            parser[f"AUTHORITYRDDATA{nAuth}"] = auth[nAuth][5]
            
    if parser["ARCOUNT"] > 0:
        add, offset = get_rr(msg, offset, parser["ARCOUNT"])
        for nAdd in range(parser["ARCOUNT"]):
            parser[f"ADDITIONALNAME{nAdd}"] = add[nAdd][0]
            parser[f"ADDITIONALTYPE{nAdd}"] = add[nAdd][1] 
            parser[f"ADDITIONALCLASS{nAdd}"] = add[nAdd][2] 
            parser[f"ADDITIONALTTL{nAdd}"] = add[nAdd][3] 
            parser[f"ADDITIONALRDLENGTH{nAdd}"] = add[nAdd][4] 
            parser[f"ADDITIONALRDDATA{nAdd}"] = add[nAdd][5] 
    
    return parser

def get_ip(type, rddata):
    ip = []
    if type == 1:    # TYPE: A
        for i in range(3, -1, -1):
            ip.append(str((rddata >> (8 * i)) & 0xFF))
        return ".".join(ip)
    elif type == 28: # TYPE: AAAA
        for i in range(7, -1, -1):
            value = str((rddata >> (16 * i)) & 0xFFFF)
            ip.append(value)
        return ":".join(ip)
    return ""

id = 0
def resolver(mensaje_consulta: bytes, ip_addr="198.41.0.4"):
    # Creamos un socket UDP
    buff_size = 2048
    new_socket_address = (ip_addr, 53)
    socket_root  = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Conectamos el socket
        socket_root.connect(new_socket_address)
        socket_root.sendto(mensaje_consulta, new_socket_address)
        # Recibimos el mensaje de respuesta
        data, _ = socket_root.recvfrom(buff_size)
        # Parseamos el mensaje
        info = pars_msg(binascii.hexlify(data).decode("utf-8"))

        while True:
            info = pars_msg(binascii.hexlify(data).decode("utf-8"))
            # Ahora nos dividimos según el caso
            # Si es hay una respuesta de tipo A dentro de la sección Answer, devolvemos los datos
            for i in range(info["ANCOUNT"]):
                if info[f"ANSWERTYPE{i}"] == 1:
                    return data
            # Si no hay respuestas de tipo A, revisamos si hay NS en AUTHORITY
            name_servers = []
            for i in range(info["NSCOUNT"]):
                if info[f"AUTHORITYTYPE{i}"] == 2:
                    name_servers.append(info[f"AUTHORITYRDDATA{i}"])
                    # Si hay NS, revisamos si hay A en ADDITIONAL
                    for i in range(info["ARCOUNT"]):
                        if info[f"ADDITIONALTYPE{i}"] == 1:
                            # Si hay A en ADDITIONAL, devolvemos los datos con la ip en ADDITIONAL
                            return resolver(mensaje_consulta, info[f"ADDITIONALRDDATA{i}"])
            # Resolvemos sobre el NS, buscando su ip
            if name_servers:
                id += 1
                id_hex = str(id.to_bytes(2, byteorder='big').hex())
                header_sin_id = "00 00 00 01 00 00 00 00 00 00 ".replace(" ","")
                header = id_hex + header_sin_id
                name_splited = name_servers[0].split(".")
                for i in range(len(name_splited)):
                    question = f"{len(name_splited[i]).hex()}" + name_splited[i].hex()
                question += "00 00 01 00 01".replace(" ", "")

                nuevo_mensaje = binascii.unhexlify(header+ question)
                nueva_respuesta = resolver(nuevo_mensaje)
                info_nuevo_msg = pars_msg(binascii.hexlify(nueva_respuesta).decode("utf-8"))
                for i in range(info_nuevo_msg["ANCOUNT"]):
                    if info_nuevo_msg[f"ANSWERTYPE{i}"] == 1:
                        nueva_ip = info_nuevo_msg[f"ANSWERRDDATA{i}"]
                        break

                data = resolver(data, ip_addr=nueva_ip)
                # se reinicia el ciclo

    finally:
        socket_root.close()
        id = 0

def pars_question(msg):
    parser = dict()
    # Header    
    headers = ["ID", "Campos", "QDCOUNT", "ANCOUNT", "NSCOUNT", "ARCOUNT"]
    for i in range(len(headers)):
        parser[headers[i]] = int(msg[i * 4:(i+1) * 4], 16)
    # Question
    offset = 24
    # Iteramos por cada pregunta que haya
    for nQuestion in range(parser["QDCOUNT"]):
        dominio, offset = get_name(msg, offset)

        # Construimos cada elemento de la secciónd de Question
        parser[f"QNAME{nQuestion}"] = dominio
        parser[f"QTYPE{nQuestion}"] = int(msg[offset:offset + 4], 16)
        parser[f"QCLASS{nQuestion}"] = int(msg[offset + 4:offset + 8], 16)
        offset += 8
    return parser


#msg = send_dns_message("8.8.4.4", 53)
# print(bytes.fromhex("636f6d").decode("utf-8")) = com
msg_cloudflare = "000080800001000200000000076578616d706c6503636f6d0000010001c00c000100010000000500046814179ac00c00010001000000050004ac4293f3"
msg_google = "000080820001000000000000076578616d706c6503636f6d0000010001"

if __name__ == "__main__":

    buff_size = 2048
    end_of_message = "\n"
    new_socket_address = ("10.0.2.15", 8000)

    print("Creando socket - Servidor")

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    server_socket.bind(new_socket_address)

    print("Esperando clientes")

    while True:
        recv_message, address = server_socket.recvfrom(buff_size)

        print(f"Se ha recibido con éxito el mensaje para el resolver: {recv_message}\n")
        respuesta = resolver(recv_message)
        if respuesta:
            print(f"Se ha resolvido la petición con éxito: {respuesta}\n")
            print("Mandando resolución al cliente\n")

            server_socket.sendto(respuesta, address)

            print("Respuesta mandada. Esperando nuevos mensajes\n")
        else:
            print("Respuesta vacia. No se mandó nada")

        print("---------------------------------------------------------------\n")

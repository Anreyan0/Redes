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
#
#a =\x00\x00
#a[0] = 00
#b ='0000'
#b[0] = 0

def get_name(msg, offset):
    name = []
    while msg[offset: offset +2] != "00":
        # Extraemos el largo
        largo = int(msg[offset:offset + 2], 16)
        # Extraemos el dominio y lo enviamos a la lista del dominio para su construccion
        name.append(bytes.fromhex(msg[offset + 2:offset + 2 + largo*2]).decode("utf-8"))
        # Actualizamos el offset para continuar leyendo
        offset += largo*2 + 2
    return ".".join(name), offset + 2

def get_rr(msg, offset, count):
    rr_list = []
    # Iteramos por cada rr que se indique 11xx
    for i in range(count):
        rr = []
        # La estructura de la sección Answer es la siguiente
        print(msg[offset: offset + 2])
        print(int(msg[offset: offset + 2], 16))
        if int(msg[offset: offset + 2], 16) >= int("C0", 16):
            # Si el primer byte es 11, significa que es un puntero a la sección de Question
            # Por lo tanto, no necesitamos leer el nombre completo, sino que podemos usar el puntero
            rr.append(int(msg[offset:offset + 4], 16))      # name
            offset += 4
        else:
            #print(count)
            # En el caso de que no sea un puntero leemos el nombre completo
            dominio, offset = get_name(msg, offset)
            print("a")
            rr.append(dominio)                              # name

        rr.append(int(msg[offset:offset+4], 16))                    # type
        rr.append(int(msg[offset+4:offset+8], 16))                  # class
        rr.append(int(msg[offset+8:offset+16], 16))                 # ttl
        rr.append(int(msg[offset+16:offset+20], 16))                # rdlength
        rr.append(int(msg[offset+20:offset+20 + rr[-1]*2], 16))     # rddata

        rr_list.append(rr)
        # Actualizamos el offset para seguir iterando
        print(rr[-2])
        offset += 20 + rr[-2]*2

    return rr_list, offset

def pars_msg(msg):
    parser = dict()
    # Header    
    headers = ["ID", "Campos", "QDCOUNT", "ANCOUNT", "NSCOUNT", "ARCOUNT"]
    for i in range(len(headers)):
        parser[headers[i]] = int(msg[i * 4:(i+1) * 4], 16)
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
        for authority in auth:
            parser["AUTHORITYNAME"] = authority[0] 
            parser["AUTHORITYTYPE"] = authority[1] 
            parser["AUTHORITYCLASS"] = authority[2] 
            parser["AUTHORITYTTL"] = authority[3] 
            parser["AUTHORITYRDLENGTH"] = authority[4] 
            parser["AUTHORITYRDDATA"] = authority[5] 
    if parser["ARCOUNT"] > 0:
        add, offset = get_rr(msg, offset, parser["ARCOUNT"])
        for additional in add:
            parser["ADDITIONALNAME"] = additional[0] 
            parser["ADDITIONALTYPE"] = additional[1] 
            parser["ADDITIONALCLASS"] = additional[2] 
            parser["ADDITIONALTTL"] = additional[3] 
            parser["ADDITIONALRDLENGTH"] = additional[4] 
            parser["ADDITIONALRDDATA"] = additional[5] 
    
    return parser

def resolver(mensaje_consulta: bytes, ip_addr):
    buff_size = 2048
    new_socket_address = (ip_addr, 53)
    socket_client  = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_client.connect(new_socket_address)
    socket_client.sendto(mensaje_consulta, new_socket_address)
    pass

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
print(bytes.fromhex("636f6d").decode("utf-8"))
msg_cloudflare = "000080800001000200000000076578616d706c6503636f6d0000010001c00c000100010000000500046814179ac00c00010001000000050004ac4293f3"
msg_google = "000080820001000000000000076578616d706c6503636f6d0000010001"
print(f"{msg_google}\n")
print(pars_msg(msg_cloudflare))

if __name__ == "__main__":

    buff_size = 1024
    end_of_message = "\n"
    new_socket_address = ("localhost", 8000)

    print("Creando socket - Servidor")

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    server_socket.bind(new_socket_address)

    print("Esperando clientes")

    while True:
        recv_message, address = server_socket.recvfrom(buff_size)

        print(f"Se ha recibido con éxito el mensaje {recv_message}")

        response_message = f"Se ha recibido con éxito el mensaje {recv_message}"

        server_socket.sendto(response_message.encode(), address)


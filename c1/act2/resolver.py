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
        name.append(bytes.fromhex(msg[offset + 2:offset + 2 + largo*2]).decode("ascii"))
        # Actualizamos el offset para continuar leyendo
        offset += largo*2 + 2
    return ".".join(name), offset + 2

def get_rr(msg, offset, count):
    rr_list = []
    # Iteramos por cada rr que se indique 1100 
    for i in range(count):
        rr = []
        # La estructura de la sección Answer es la siguiente
        if int(msg[offset: offset + 2], 16) >= int("C000", 16):
            # Si el primer byte es 11, significa que es un puntero a la sección de Question
            # Por lo tanto, no necesitamos leer el nombre completo, sino que podemos usar el puntero
            rr.append(int(msg[offset:offset + 4], 16))
        else:
            dominio, offset = get_name(msg, offset)
            rr.append(dominio)

        rr.append(int(msg[offset:offset+4], 16))
        rr.append(int(msg[offset+4:offset+8], 16))
        rr.append(int(msg[offset+8:offset+16], 16))
        rr.append(int(msg[offset+16:offset+20], 16))
        rr.append(msg[offset+20:offset+20 + rr[-1]*2])

        rr_list.append(rr)
        # Actualizamos el offset para seguir iterando
        offset += 24 + rr[-1]*2

    return rr_list, offset

def pars_msg(msg):
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
        parser[f"QNAME{nQuestion}"] = ".".join(dominio)
        parser[f"QTYPE{nQuestion}"] = int(msg[offset:offset + 4], 16)
        parser[f"QCLASS{nQuestion}"] = int(msg[offset + 4:offset + 8], 16)
        offset += 8
    
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

    auth, offset = get_rr(msg, offset, 1)
    add, offset = get_rr(msg, offset, 1)
    for authority in auth:
        parser["AUTHORITYNAME"] = authority[0] 
        parser["AUTHORITYTYPE"] = authority[1] 
        parser["AUTHORITYCLASS"] = authority[2] 
        parser["AUTHORITYTTL"] = authority[3] 
        parser["AUTHORITYRDLENGTH"] = authority[4] 
        parser["AUTHORITYRDDATA"] = authority[5] 

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

msg = send_dns_message("8.8.4.4", 53)
print(f"{msg}\n")
print(pars_msg(msg))

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


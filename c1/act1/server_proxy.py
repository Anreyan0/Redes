import socket
import json
import sys


# esta función se encarga de recibir el mensaje completo desde el cliente
# en caso de que el mensaje sea más grande que el tamaño del buffer 'buff_size', esta función va esperar a que
# llegue el resto. Para saber si el mensaje ya llegó por completo, se busca el caracter de fin de mensaje (parte de nuestro protocolo inventado)
 
def receive_full_client_http_message(connection_socket, buff_size):

    # recibimos la primera parte del mensaje
    http_message = connection_socket.recv(buff_size)
    full_http_message = http_message

    # secuencia en bytes que indica que recibimos todo el HEAD
    end_of_HEAD = b"\r\n\r\n"

    # entramos a un while si aún no se recibe todo el HEAD
    # el while terminará cuando se encuentren los bytes que representan "\r\n\r\n"
    while end_of_HEAD not in full_http_message:
        # recibimos un nuevo trozo del mensaje
        http_message = connection_socket.recv(buff_size)

        # lo añadimos al mensaje "completo"
        full_http_message += http_message

    # finalmente retornamos el mensaje
    return full_http_message
 
def receive_full_server_http_message(connection_socket, buff_size):

    # recibimos la primera parte del mensaje
    http_message = connection_socket.recv(buff_size)
    full_http_message = http_message

    # secuencia en bytes que indica que recibimos todo el HEAD
    end_of_HEAD = b"\r\n\r\n"

    # entramos a un while si aún no se recibe todo el HEAD
    # el while terminará cuando se encuentren los bytes que representan "\r\n\r\n"
    while end_of_HEAD not in full_http_message:
        # recibimos un nuevo trozo del mensaje
        http_message = connection_socket.recv(buff_size)

        # lo añadimos al mensaje "completo"
        full_http_message += http_message

    # finalmente retornamos el mensaje
    caught_bytes_of_body = len(full_http_message.split(b"\r\n\r\n")[1])
    
    parsed_http = parse_HTTP_message(full_http_message)
    if "Content-Length" in parsed_http:
        body_length = parsed_http["Content-Length"]
        rest_of_body_message = b""
        difference = int(body_length) - caught_bytes_of_body

        while len(rest_of_body_message) < difference:
            body_message = connection_socket.recv(buff_size)
            rest_of_body_message += body_message
        full_http_message += rest_of_body_message

    return full_http_message


def split_head_and_body(http_message: bytes):
    return http_message.split(b"\r\n\r\n")


def check_forbidden(domain):
    return

def create_forbidden_http():
    return


#def get_content_length(message, end_sequence):
#    return message.endswith(end_sequence)
 
def parse_HTTP_message(http_message: bytes):
    decoded_head = http_message.decode()
    # solo debería recibir REQUEST, así que es solo un HEAD
    split_http = decoded_head.split("\r\n\r\n")[0]
    split_http = split_http.split("\r\n")
    print(" -> Se ha parseado el siguiente mensaje: ", split_http)
    # Iteramos en el header para guardarlo en un diccionario
    http_dict = dict()
    http_dict["start line"] = split_http[0] 
    for header in split_http[1:]:
        type_and_header = header.split(": ", maxsplit=1)
        http_dict[type_and_header[0]] = type_and_header[1]
    
    return http_dict

def create_HTTP_message(http_dict: dict):
    http_message = ""
    start_line = "HTTP/1.1 200 OK\r\n"
    html = "<html><body><h1>Hola mundo</h1></body></html>"
    html_length = len(html.encode())
    http_message += start_line
    http_message += "Content-Type: " + http_dict["Accept"] + "\r\n"
    http_message += "Content-Length: " + str(html_length) + "\r\n"
    # http_message += f"X-ElQuePregunta: {http_dict["json_name"]}\r\n\r\n"
    http_message += html
    # for key, value in http_dict.items():
    #    http_message += f"{key}: {value}\r\n"
    # http_message += "\r\n"

    return http_message.encode()

def add_name_to_header(msg: bytes):
    # parseamos el mensaje
    parse = parse_HTTP_message(msg)
    # lo agregamos como nombre extra al dict
    # parse["json_name"] = name
    # creamos la respuesta con el nuevo header
    new_message = create_HTTP_message(parse)
    return new_message
    
if __name__ == "__main__":
    #verificamos si se entregó un nombre de configuración
    #if len(sys.argv) < 3:
    #    print("Falta el nombre del archivo de configuración")
    #    sys.exit(1)

    # definimos el tamaño del buffer de recepción y la secuencia de fin de mensaje
    buff_size = 16
    end_of_message = "\n"
    new_socket_address = ('0.0.0.0', 8000)
    #nombre = sys.argv[1]
    #config = sys.argv[2]
 
    print('Creando socket - Servidor')
    # armamos el socket
    # los parámetros que recibe el socket indican el tipo de conexión
    # socket.SOCK_STREAM = socket orientado a conexión
    listener_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
 
    # le indicamos al server socket que debe atender peticiones en la dirección address
    # para ello usamos bind
    listener_socket.bind(new_socket_address)
 
    # luego con listen (función de sockets de python) le decimos que puede
    # tener hasta 3 peticiones de conexión encoladas
    # si recibiera una 4ta petición de conexión la va a rechazar
    listener_socket.listen(3)
 
    # nos quedamos esperando a que llegue una petición de conexión
    print('... Esperando clientes')
    while True:
        print("conectado")
        # cuando llega una petición de conexión la aceptamos
        # y se crea un nuevo socket que se comunicará con el cliente
        client_proxy_socket, client_proxy_socket_address = listener_socket.accept()
        
        recv_message = receive_full_client_http_message(client_proxy_socket, buff_size)
        parsed_message = parse_HTTP_message(recv_message)

        print(f' -> Se ha recibido el siguiente mensaje: {recv_message}')
        # crear conexión con el server
        server_connection_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_connection_socket.connect((parsed_message["Host"], 80))

        # luego recibimos el mensaje usando la función que programamos
        # esta función entrega el mensaje en string (no en bytes) y sin el end_of_message
 

        # respondemos indicando que recibimos el mensaje
        response_message = add_name_to_header(recv_message)
 
        server_connection_socket.send(recv_message)

        server_response = receive_full_server_http_message(server_connection_socket, buff_size)

        print(f' <- Se ha recibido el siguiente mensaje del server: {server_response}')
        # el mensaje debe pasarse a bytes antes de ser enviado, para ello usamos encode
        client_proxy_socket.send(server_response)
 
        # cerramos la conexión
        # notar que la dirección que se imprime indica un número de puerto distinto al 5000
        client_proxy_socket.close()
        print(f"conexión con {new_socket_address} ha sido cerrada")
 
        # seguimos esperando por si llegan otras conexiones
import socket
import json
import sys
import base64

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

    # Parseamos el mensaje guardándolo en un diccionario para su acceso
    parsed_http = parse_HTTP_message(full_http_message)
    if "Content-Length" in parsed_http:
        body_length = parsed_http["Content-Length"]
        rest_of_body_message = b""
        # Contamos los bytes que pasaron extra después del fin del head
        difference = int(body_length) - caught_bytes_of_body

        # Contamos los bytes hasta que lso hayamos recopilado todos
        while len(rest_of_body_message) < difference:
            body_message = connection_socket.recv(buff_size)
            rest_of_body_message += body_message
        full_http_message += rest_of_body_message

    # Retornamos el mensaje completo
    return full_http_message


def split_head_and_body(http_message: bytes):
    # Separamos el Head del Body según los bytes que indican el final del Head en el mensaje HTTP
    return http_message.split(b"\r\n\r\n")

def get_domain(start_line):
    # Separamos la Start line por espacios y luego desglosamos la url para obtener el dominio solicitado
    splited_start_line = start_line.split(" ")
    domain = splited_start_line[1].split("//", maxsplit=1)[1].strip("/")
    print(f"\n{domain}\n")
    return domain

def check_forbidden(domain, json_file):
    #  Abrimos el archivo para verificar la lista de sitios prohibidos
    with open(f"{json_file}.json", "r", encoding="utf-8") as file:
        data = json.load(file)

    # Extraemos los sitios bloqueados y revisamos si el dominio está permitido
    list_of_forbidden_sites = data["blocked"]
    if domain in list_of_forbidden_sites:
        return True
    return False

def create_forbidden_http():
    # Start Line de página prohibida
    http_message = "HTTP/1.1 403 Forbidden\r\n"
    # Cuerpo del mensaje
    body_message = f"<!DOCTYPE html><html><body><img src='./all_in.jpg' alt='Imagen Local'></body></html>"
    # Headers necesarios para la respuesta al cliente
    http_message += "Content-Length: " + str(len(body_message.encode())) + "\r\n"
    http_message += "Content-Type: text/html\r\n\r\n"
    http_message += body_message
    return http_message.encode()

def create_http_image():
    # Abrimos la imagen para guardar los datos
    with open("all_in.jpg", "rb") as image:
        encoded_image = image.read()
    # Creamos la respuesta del servidor esperando la imagen
    msg = f"HTTP/1.1 200 OK\r\nContent-Type: image/jpg\r\nContent-Length: {len(encoded_image)}\r\n\r\n"
    
    return msg.encode() + encoded_image

def replace_forbidden_words(server_response, json_file):
    # Abrimos el archivo para extraer los datos
    with open(f"{json_file}.json", "r", encoding="utf-8") as file:
            data = json.load(file)
    # Vemos las palabras prohibidas
    forbidden_words = data["forbidden_words"]
    # Obtenemos head y body de la respuesta del servidor
    message_as_list = split_head_and_body(server_response)
    head = message_as_list[0]
    html = message_as_list[1]
    # Reemplazamos cada coincidencia dentro del body
    for dicts in forbidden_words:
        for key, value in dicts.items():
            replacement = value.encode()
            html = html.replace(key.encode(), replacement)

    return head + b"\r\n\r\n" + html
 
def parse_HTTP_message(http_message: bytes):
    decoded_head = http_message.decode()
    # solo debería recibir REQUEST, así que es solo un HEAD
    # Separamos por head y body
    split_http = decoded_head.split("\r\n\r\n")[0]
    # Separamos cada header
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
    # Comenzamos con la Start Line
    http_message += http_dict["start line"] + "\r\n"
    # Incluimos el resto de headers
    http_message += "Accept: " + http_dict["Accept"] + "\r\n"
    http_message += "Host: " + http_dict["Host"] + "\r\n"
    # Añadimos un header extra
    http_message += "X-ElQuePregunta: Mania\r\n\r\n"

    return http_message.encode()

def create_response_msg(msg: bytes):
    # parseamos el mensaje
    parse = parse_HTTP_message(msg)
    # creamos la respuesta con el nuevo header
    new_message = create_HTTP_message(parse)
    return new_message
    
if __name__ == "__main__":

    # definimos el tamaño del buffer de recepción y la secuencia de fin de mensaje
    buff_size = 16
    end_of_message = "\n"
    new_socket_address = ('127.0.0.1', 8000)
 
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

        # Recibimos y parseamos el mensaje
        recv_message = receive_full_client_http_message(client_proxy_socket, buff_size)
        parsed_message = parse_HTTP_message(recv_message)
        # En el caso de que haya una solicitud CONNECT la ignoraremos para evitar problemas con el desarrollo de la actividad
        if "CONNECT" in parsed_message["start line"]:
            continue

        # Obtenemos el dominio y verificamos si está prohibido
        domain = get_domain(parsed_message["start line"])
        if check_forbidden(domain, "config"):
            print(f" -> Se ha recibido un mensaje de un sitio bloqueado: {domain}")
            forbidden_message = create_forbidden_http()
            # Enviamos un mensaje al cliente del sitio prohibido
            client_proxy_socket.send(forbidden_message)
            continue
        # En el caso de que el nombre de la imagen venga en la Start Line asumiremos que el servidor está solicitando la misma imagen
        elif "all_in.jpg" in parsed_message["start line"]:
                # Creamos el mensaje HTTP y lo enviamos
                msg = create_http_image()
                client_proxy_socket.send(msg)
                print("Se ha enviado all_in")
                # Ya no necesitamos seguir hablando con el cliente sobre este sitio web bloqueado
                client_proxy_socket.close()
                print(f"conexión con {client_proxy_socket_address} ha sido cerrada")
                continue

        print(f' -> Se ha recibido el siguiente mensaje: {recv_message}')

        # crear conexión con el server
        server_connection_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # print(f"{parsed_message['Host']}")
        server_connection_socket.connect((parsed_message["Host"], 80))

        # luego recibimos el mensaje usando la función que programamos
        # esta función entrega el mensaje en string (no en bytes) y sin el end_of_message
 

        # respondemos indicando que recibimos el mensaje
        response_message = create_response_msg(recv_message)

        print(f' Se ha creado la siguiente respuesta al server: {response_message}')
 
        # Enviamos el mensaje al sevidor
        server_connection_socket.send(response_message)

        server_response = receive_full_server_http_message(server_connection_socket, buff_size)

        print(f' <- Se ha recibido el siguiente mensaje del server: {server_response}')

        # Reemplazamos las palabras prohibidas
        response_without_forbidden_words = replace_forbidden_words(server_response, "config")
        if response_without_forbidden_words != server_response:
            print(f' <- Se han modificado las palabras prohibidas de la respuesta del server: {response_without_forbidden_words}')

        # el mensaje debe pasarse a bytes antes de ser enviado, para ello usamos encode
        client_proxy_socket.send(response_without_forbidden_words)
 
        # cerramos la conexión
        # notar que la dirección que se imprime indica un número de puerto distinto al 5000
        client_proxy_socket.close()
        print(f"conexión con {new_socket_address} ha sido cerrada")
 
        # seguimos esperando por si llegan otras conexiones
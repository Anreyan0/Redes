import socket
import json
import sys


# esta función se encarga de recibir el mensaje completo desde el cliente
# en caso de que el mensaje sea más grande que el tamaño del buffer 'buff_size', esta función va esperar a que
# llegue el resto. Para saber si el mensaje ya llegó por completo, se busca el caracter de fin de mensaje (parte de nuestro protocolo inventado)
 
def receive_full_http_message(connection_socket, buff_size):

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
 

def get_head_body(message):
    message.decode().split("\r\n\r\n")

#def get_content_length(message, end_sequence):
#    return message.endswith(end_sequence)
 
def parse_HTTP_message(http_message: bytes):
    decoded_head = http_message.decode()
    # solo debería recibir REQUEST, así que es solo un HEAD
    split_http = decoded_head.removesuffix("\r\n\r\n").split("\r\n")
    
    # Iteramos en el header para guardarlo en un diccionario
    http_dict = dict()
    http_dict["start line"] = split_http[0] 
    for header in split_http[1:]:
        type_and_header = header.split(": ", maxsplit=1)
        http_dict[type_and_header[0]] = type_and_header[1]
    
    print(http_dict)
    return http_dict

def create_HTTP_message(http_dict: dict):
    http_message = ""
    start_line = "HTTP/1.1 200 OK\r\n"
    html = "<html><body><h1>Hola mundo</h1></body></html>"
    html_length = len(html.encode())
    http_message += start_line
    http_message += "Content-Type: " + http_dict["Accept"] + "\r\n"
    http_message += "Content-Length: " + str(html_length) + "\r\n\r\n"
    http_message += html
    # for key, value in http_dict.items():
    #    http_message += f"{key}: {value}\r\n"
    # http_message += "\r\n"

    return http_message.encode()
     
if __name__ == "__main__":
    # definimos el tamaño del buffer de recepción y la secuencia de fin de mensaje
    buff_size = 16
    end_of_message = "\n"
    new_socket_address = ('192.168.56.102', 5000)
 
    print('Creando socket - Servidor')
    # armamos el socket
    # los parámetros que recibe el socket indican el tipo de conexión
    # socket.SOCK_STREAM = socket orientado a conexión
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
 
    # le indicamos al server socket que debe atender peticiones en la dirección address
    # para ello usamos bind
    server_socket.bind(new_socket_address)
 
    # luego con listen (función de sockets de python) le decimos que puede
    # tener hasta 3 peticiones de conexión encoladas
    # si recibiera una 4ta petición de conexión la va a rechazar
    server_socket.listen(3)
 
    # nos quedamos esperando a que llegue una petición de conexión
    print('... Esperando clientes')
    while True:
        # cuando llega una petición de conexión la aceptamos
        # y se crea un nuevo socket que se comunicará con el cliente
        new_socket, new_socket_address = server_socket.accept()
 
        # luego recibimos el mensaje usando la función que programamos
        # esta función entrega el mensaje en string (no en bytes) y sin el end_of_message
        recv_message = receive_full_http_message(new_socket, buff_size)
 
        print(f' -> Se ha recibido el siguiente mensaje: {recv_message}')
 
        # respondemos indicando que recibimos el mensaje
        response_message = create_HTTP_message(parse_HTTP_message(recv_message))
 
        # el mensaje debe pasarse a bytes antes de ser enviado, para ello usamos encode
        new_socket.send(response_message)
 
        # cerramos la conexión
        # notar que la dirección que se imprime indica un número de puerto distinto al 5000
        new_socket.close()
        print(f"conexión con {new_socket_address} ha sido cerrada")
 
        # seguimos esperando por si llegan otras conexiones
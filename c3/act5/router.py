import sys
import socket
# Realizar round robbin con un diccionario y listas circulares para leer las rutas realizadas en el main

def parse_packet(IP_packet: bytes):
    dicc_parseo = dict()
    dicc_parseo["IP"] = socket.inet_ntoa(IP_packet[:4])
    dicc_parseo["Puerto"] = int.from_bytes(IP_packet[4:6], byteorder='big')
    dicc_parseo["Mensaje"] = IP_packet[6:]
    return dicc_parseo

def create_packet(parsed_IP_packet):
    ipv4 = socket.inet_aton(parsed_IP_packet["IP"])
    puerto = parsed_IP_packet["Puerto"].to_bytes(2)
    msg = parsed_IP_packet["Mensaje"]
    return ipv4 + puerto + msg

def check_routes(routes_file_name: str, destination_address: tuple[str, int]) -> tuple[str, int]:
    with open(routes_file_name, "r") as f:
        rutas = f.read()
    rutas = rutas.split("\n")
    
    for ruta in rutas:
        ruta_elements = ruta.split(" ")
        puerto_inicial = int(ruta_elements[1])
        puerto_final = int(ruta_elements[2])
        if puerto_inicial <= destination_address[1] <= puerto_final:
            return (ruta_elements[3], int(ruta_elements[4]))

    return None

if __name__ == "__main__":

    if len(sys.argv) < 3:
        raise Exception("No se ha especificado una dirección y puerto")
    elif len(sys.argv) < 4:
        raise Exception("No se ha especificado una tabla de rutas")

    ip = sys.argv[1]
    puerto = int(sys.argv[2])
    with open(sys.argv[3], "r") as f:
            rutas = f.read()

    rutas_dict = {}
    for ruta in rutas:
        
    address = (ip, puerto)
    buff_size = 2048

    router_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    router_socket.bind(address)

    print(f"ip: {ip}; puerto: {puerto}; rutas: {rutas}\n")

    print("Prueba de check_routes() con destino dentro del rango de red")
    destination_address = ("127.0.0.1", 8884)
    print(f"Resultado de check_routes(): {check_routes(sys.argv[3], destination_address)}\n")

    print("Prueba de check_routes() con destino fuera del rango de red")
    destination_address = ("127.0.0.1", 9000)
    print(f"Resultado de check_routes(): {check_routes(sys.argv[3], destination_address)}\n")


    print("Esperando mensajes\n")
    
    while True:
        recv_packet, recv_address = router_socket.recvfrom(buff_size)
        parsed_packet = parse_packet(recv_packet)
        destination_address = (parsed_packet["IP"], parsed_packet["Puerto"])

        if address == destination_address:
            print(f"Mensaje recibido: {parsed_packet["Mensaje"]}")
        else:
            forwarding_route = check_routes(sys.argv[3], destination_address)
            if forwarding_route is not None:
                router_socket.sendto(recv_packet, forwarding_route)
                print(f"Redirigiendo paquete {recv_packet} con destino final {destination_address} desde {address} hacia {forwarding_route}")
            else:
                print(f"No hay rutas hacia {destination_address} para paquete {parsed_packet}")

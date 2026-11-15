import sys
import socket
# Realizar round robbin con un diccionario y listas circulares para leer las rutas realizadas en el main

def parse_packet(IP_packet: bytes):
    dicc_parseo = dict()
    dicc_parseo["IP"] = socket.inet_ntoa(IP_packet[:4])
    dicc_parseo["Puerto"] = int.from_bytes(IP_packet[4:6], byteorder='big')
    dicc_parseo["TTL"] = IP_packet[6]
    dicc_parseo["ID"] = IP_packet[7]
    dicc_parseo["Offset"] = int.from_bytes(IP_packet[8:12], byteorder='big')
    dicc_parseo["Tamaño"] = int.from_bytes(IP_packet[12:16], byteorder='big')
    dicc_parseo["FLAG"] = IP_packet[16]
    dicc_parseo["Mensaje"] = IP_packet[17:]
    return dicc_parseo

def create_packet(parsed_IP_packet):
    ipv4 = socket.inet_aton(parsed_IP_packet["IP"])
    puerto = parsed_IP_packet["Puerto"].to_bytes(2)
    ttl = (parsed_IP_packet["TTL"]).to_bytes(1)
    id = parsed_IP_packet["ID"].to_bytes(1)
    offset = parsed_IP_packet["Offset"].to_bytes(4)
    tamaño = parsed_IP_packet["Tamaño"].to_bytes(4)
    flag = parsed_IP_packet["FLAG"].to_bytes(1)
    msg = parsed_IP_packet["Mensaje"]
    return ipv4 + puerto + ttl + id + offset + tamaño + flag + msg

def check_routes(routes_file_name: str, destination_address: tuple[str, int]) -> tuple[str, int]:
    with open(routes_file_name, "r") as f:
        rutas = f.read()
    rutas = rutas.split("\n")
    for ruta in rutas:
        ruta_elements = ruta.split(" ")
        puerto_inicial = int(ruta_elements[1])
        puerto_final = int(ruta_elements[2])
        print(rutas_dict[(puerto_inicial, puerto_final)][0])
        if puerto_inicial <= destination_address[1] <= puerto_final:
            puntero = rutas_dict[(puerto_inicial, puerto_final)][1]
            rutas_dict[(puerto_inicial, puerto_final)][1] = (rutas_dict[(puerto_inicial, puerto_final)][1] + 1) % len(rutas_dict[(puerto_inicial, puerto_final)][0])
            next_hop_address = (rutas_dict[(puerto_inicial, puerto_final)][0][puntero][0],
                                rutas_dict[(puerto_inicial, puerto_final)][0][puntero][1])
            MTU = rutas_dict[(puerto_inicial, puerto_final)][0][puntero][2]
            return (next_hop_address, MTU)

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
    for ruta in rutas.split("\n"):
        ruta_elements = ruta.split(" ")
        print(ruta_elements)
        puerto_inicial = int(ruta_elements[1])
        puerto_final = int(ruta_elements[2])
        MTU = int(ruta_elements[5])
        if (puerto_inicial, puerto_final) in rutas_dict:
            rutas_dict[(puerto_inicial, puerto_final)][0].append((ruta_elements[3], int(ruta_elements[4]), MTU))
        else:
            rutas_dict[(puerto_inicial, puerto_final)] = [[(ruta_elements[3], int(ruta_elements[4]), MTU)], 0]
        print(f"dict: {rutas_dict}")
        
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

        if parsed_packet["TTL"] == 0:
            print("Se recibió paquete [paquete_ip] con TTL 0")
            continue

        if address == destination_address:
            print(f"Mensaje recibido: {parsed_packet["Mensaje"]}")
        else:
            forwarding_route_and_MTU = check_routes(sys.argv[3], destination_address)
            forwarding_route = forwarding_route_and_MTU[0]
            MTU = forwarding_route_and_MTU[1]
            print(f"forwarding route {forwarding_route}")
            if forwarding_route is not None:
                print(parsed_packet, forwarding_route)
                parsed_packet["TTL"] -= 1
                router_socket.sendto(create_packet(parsed_packet), forwarding_route)
                print(f"Redirigiendo paquete {create_packet(parsed_packet)} con destino final {destination_address} desde {address} hacia {forwarding_route}\n")
            else:
                print(f"No hay rutas hacia {destination_address} para paquete {parsed_packet}\n")

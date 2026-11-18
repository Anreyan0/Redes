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

def fragment_IP_packet(IP_packet, MTU):
    packet_size = len(IP_packet)
    if packet_size <= MTU:
        return [IP_packet]
    else:
        msg_MTU = MTU - 17 # MTU del mensaje como tal, sin considerar los headers
        parsed_ip_packet = parse_packet(IP_packet)
        msg_size = parsed_ip_packet["Tamaño"]

        msg_fragments = [parsed_ip_packet["Mensaje"][i:(i+msg_MTU)] for i in range(0, msg_size, msg_MTU)]
        number_of_fragments = len(msg_fragments)
        current_fragment = 0
        offset = parsed_ip_packet["Offset"]
        flag = 1
        ip_fragments = []
        for fragment in msg_fragments:
            current_fragment += 1
            if (current_fragment == number_of_fragments) and (parsed_ip_packet["FLAG"] == 0):
                flag = 0

            fragment_ip = socket.inet_aton(parsed_ip_packet["IP"])
            fragment_port = parsed_ip_packet["Puerto"].to_bytes(2)
            fragment_ttl = (parsed_ip_packet["TTL"]).to_bytes(1)
            fragment_id = parsed_ip_packet["ID"].to_bytes(1)
            fragment_offset = offset.to_bytes(4)
            fragment_tamaño = len(fragment).to_bytes(4)
            fragment_flag = flag.to_bytes(1)
            fragment_msg = fragment
            ip_fragment = fragment_ip + fragment_port + fragment_ttl + fragment_id + fragment_offset + fragment_tamaño + fragment_flag + fragment_msg
            ip_fragments.append(ip_fragment)

            offset += len(fragment)

        return ip_fragments

def reassemble_IP_packet(fragment_list):
    fragment_list_len = len(fragment_list)
    if fragment_list_len == 1:
        parsed_frag = parse_packet(fragment_list[0])
        if (parsed_frag["Offset"] != 0): # Si se cumple, recibimos una lista incompleta de fragmentos
            return None
        elif (parsed_frag["FLAG"] == 1): # Si el offset es 0, pero el FLAG indica que todavía debe recibir más, también está incompleta
            return None
        else:
            return fragment_list[0]
    else:
        ordered_fragments = sorted(fragment_list, key=lambda fragment: int.from_bytes(fragment[8:12], byteorder='big'))

        # Checkeando si llegó el mensaje completo
        first_parsed_frag = parse_packet(ordered_fragments[0])
        final_parsed_frag = parse_packet(ordered_fragments[-1])
        if (first_parsed_frag["Offset"] == 0) and (final_parsed_frag["FLAG"] == 0):
            for i in range(0, len(ordered_fragments) - 1):
                current_parsed_frag = parse_packet(ordered_fragments[i])
                next_parsed_frag = parse_packet(ordered_fragments[i+1])
                if (next_parsed_frag["Offset"] - current_parsed_frag["Offset"]) > len(current_parsed_frag["Mensaje"]):
                    return None
        else:
            return None

        total_msg = b""
        for fragment in ordered_fragments:
            total_msg += fragment[17:]
        total_len = len(total_msg)
        parsed_frag = parse_packet(ordered_fragments[0])

        fragment_ip = socket.inet_aton(parsed_frag["IP"])
        fragment_port = parsed_frag["Puerto"].to_bytes(2)
        fragment_ttl = (parsed_frag["TTL"]).to_bytes(1)
        fragment_id = parsed_frag["ID"].to_bytes(1)
        fragment_offset = (0).to_bytes(4)
        fragment_tamaño = total_len.to_bytes(4)
        fragment_flag = (0).to_bytes(1)
        fragment_msg = total_msg
        ip_fragment = fragment_ip + fragment_port + fragment_ttl + fragment_id + fragment_offset + fragment_tamaño + fragment_flag + fragment_msg
        return ip_fragment



if __name__ == "__main__":

    if len(sys.argv) < 3:
        raise Exception("No se ha especificado una dirección y puerto")
    elif len(sys.argv) < 4:
        raise Exception("No se ha especificado una tabla de rutas")

    ip = sys.argv[1]
    puerto = int(sys.argv[2])
    with open(sys.argv[3], "r") as f:
            rutas = f.read()

    # Sección de diccionario de rutas
    rutas_dict = {}
    for ruta in rutas.split("\n"):
        ruta_elements = ruta.split(" ")
        puerto_inicial = int(ruta_elements[1])
        puerto_final = int(ruta_elements[2])
        MTU = int(ruta_elements[5])
        if (puerto_inicial, puerto_final) in rutas_dict:
            rutas_dict[(puerto_inicial, puerto_final)][0].append((ruta_elements[3], int(ruta_elements[4]), MTU))
        else:
            rutas_dict[(puerto_inicial, puerto_final)] = [[(ruta_elements[3], int(ruta_elements[4]), MTU)], 0]

    # Sección diccionario de fragmentos
    fragments_dict = {}
    
    address = (ip, puerto)
    buff_size = 2048

    router_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    router_socket.bind(address)

    print(f"ip: {ip}; puerto: {puerto}; rutas: {rutas}\n")
    print(f"Diccionario de rutas: {rutas_dict}\n")

    print("Prueba de check_routes() con destino dentro del rango de red")
    destination_address = ("127.0.0.1", 8884)
    print(f"Resultado de check_routes(): {check_routes(sys.argv[3], destination_address)}\n")

    print("Prueba de check_routes() con destino fuera del rango de red")
    destination_address = ("127.0.0.1", 9000)
    print(f"Resultado de check_routes(): {check_routes(sys.argv[3], destination_address)}\n")

    print("Prueba de fragment_IP_packet() con paquete de largo <= MTU")
    ip_packet_test = socket.inet_aton("127.0.0.1") + (9000).to_bytes(2) + (200).to_bytes(1) + (67).to_bytes(1) + (0).to_bytes(4) + (200).to_bytes(4) + (1).to_bytes(1) + ("A" * 100).encode()
    MTU_test = 300
    print(f"Resultado de fragment_IP_packet(): {fragment_IP_packet(ip_packet_test, MTU_test)}\n")

    print("Prueba de fragment_IP_packet() con paquete de largo > MTU")
    ip_packet_test = socket.inet_aton("127.0.0.1") + (9000).to_bytes(2) + (200).to_bytes(1) + (67).to_bytes(1) + (0).to_bytes(4) + (100).to_bytes(4) + (1).to_bytes(1) + ("A" * 100).encode()
    MTU_test = 30
    print(f"Resultado de fragment_IP_packet(): {fragment_IP_packet(ip_packet_test, MTU_test)}\n")


    print("Esperando mensajes\n")
    
    while True:
        recv_packet, recv_address = router_socket.recvfrom(buff_size)
        parsed_packet = parse_packet(recv_packet)
        destination_address = (parsed_packet["IP"], parsed_packet["Puerto"])

        if address == destination_address:
            if parsed_packet["TTL"] == 0:
                print(f"Se recibió un paquete de ID = {parsed_packet["ID"]} con TTL 0")
                continue
            
            id_str = str(parsed_packet["ID"])
            print(f"Se recibió un paquete de ID = {parsed_packet["ID"]}")
            if id_str in fragments_dict:
                fragments_dict[id_str].append(recv_packet)
            else:
                fragments_dict[id_str] = [recv_packet]

            if (reassemble_IP_packet(fragments_dict[id_str])) is not None:
                complete_parsed_packet = parse_packet(reassemble_IP_packet(fragments_dict[id_str]))
                print(f"Paquete IP completo recibido: {complete_parsed_packet["Mensaje"]}\n")
            else:
                print(f"Aún no llega el mensaje completo de ID = {parsed_packet["ID"]}")
            
        else:
            print(f"Se recibió un paquete de ID = {parsed_packet["ID"]} para otro router")
            forwarding_route_and_MTU = check_routes(sys.argv[3], destination_address)
            forwarding_route = forwarding_route_and_MTU[0]
            print(f"forwarding route {forwarding_route}")
            if forwarding_route is not None:
                MTU = forwarding_route_and_MTU[1]
                parsed_packet["TTL"] -= 1

                fragments = fragment_IP_packet(create_packet(parsed_packet), MTU)
                print(f"Número de fragmentos a enviar: {len(fragments)}")
                for ip_fragment in fragments:
                    router_socket.sendto(ip_fragment, forwarding_route)
                    print(f"Redirigiendo fragmento {parse_packet(ip_fragment)} con destino final {destination_address} desde {address} hacia {forwarding_route}\n")
            else:
                print(f"No hay rutas hacia {destination_address} para paquete {parsed_packet}\n")

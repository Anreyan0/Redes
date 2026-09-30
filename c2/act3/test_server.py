import socket_tcp_2

address = ("localhost", 5000)

# server 
server_socketTCP = socket_tcp_2.SocketTCP()
server_socketTCP.bind(address)
connection_socketTCP, new_address = server_socketTCP.accept()
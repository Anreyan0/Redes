import socket_tcp

address = ("localhost", 5000)

# server 
server_socketTCP = socket_tcp.SocketTCP()
server_socketTCP.bind(address)
connection_socketTCP, new_address = server_socketTCP.accept()
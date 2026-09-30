import socket_tcp

address = ("localhost", 5000)

# client
client_socketTCP = socket_tcp.SocketTCP()
client_socketTCP.connect(address)
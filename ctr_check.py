import socket
import re
rule = re.compile(r"(\d+)([.\.])(\d+)([.\.])(\d+)([.\.])(\d+)")

while True:
    ip = raw_input("IP : ")

    if(rule.match(ip)):
        print "Attempting connection to "+ip+" at port 8098"

        clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientsocket.connect((ip, 8089))
        clientsocket.send("HELLO")
        data = clientsocket.recv(1024)
        print data

        clientsocket.close()
    else:
        print "wrong ip"

import socket
import time
servers = {"10.0.0.1","10.0.0.2","10.0.0.3"}
n=0
while True:

    for ip in servers:
        #print "Attempting connection to "+ip+" at port 8098"
        clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        clientsocket.connect((ip, 8089))
        clientsocket.send("HELLO")
        data = clientsocket.recv(1024)
        print "IP = "+ip+" SEQ = "+str(n)+" "+data

        clientsocket.close()
    n+=1
    time.sleep(2)

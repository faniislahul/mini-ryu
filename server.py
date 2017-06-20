import socket
from thread import start_new_thread
import json
import psutil

def dosomething(conn, addr):
        data = conn.recv(1024)
        print data +" from "+ addr[0] + " and port "+str(addr[1])
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        msg = json.dumps({"cpu" : cpu,"mem" : mem})
        conn.send(msg)

serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serversocket.bind(('0.0.0.0', 8089))
serversocket.listen(5)


while True:
    conn, addr = serversocket.accept();
    print addr[0] + " connected on "+ str(addr[1])

    start_new_thread(dosomething,(conn,addr,))
conn.close()
serversocket.close()

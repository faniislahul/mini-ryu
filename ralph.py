import socket
import time
from threading import Thread
import thread
import json

servers = {"10.0.0.1","10.0.0.2","10.0.0.3"}
stats = {"cpu": 0, "mem" : 0, "rtt" : 0}
arr = {'10.0.0.1' : stats,'10.0.0.2' : stats,'10.0.0.3' : stats}

def server_check(ip):
    global arr
    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    clientsocket.settimeout(2)
    #print ip
    try:
        clientsocket.connect((ip,8089))
        clientsocket.send("REQ")
        start = time.time()
        raw = clientsocket.recv(1024)
        data = json.loads(raw)
        end = time.time()
        rtt = end-start
        arr[ip]['cpu'] = data['cpu']
        arr[ip]['mem'] = data['mem']
        arr[ip]['rtt'] = rtt
        #print str(rtt)
        print "IP = "+ip+" RTT = "+str(rtt)+" CPU = "+str(data["cpu"])+" MEM = "+str(data["mem"])
        #print "IP = "+ip+" RTT = "+str(arr[ip]['rtt'])+" CPU = "+str(arr[ip]["cpu"])+" MEM = "+str(arr[ip]["mem"])
        clientsocket.close()
    except socket.timeout:
        arr[ip]['cpu'] = 0
        arr[ip]['mem'] = 0
        arr[ip]['rtt'] = 0
        print "IP = "+ip+" REQUEST TIMEOUT"
        clientsocket.close()
    except socket.error:
        arr[ip]['cpu'] = 0
        arr[ip]['mem'] = 0
        arr[ip]['rtt'] = 0
        print "IP = "+ip+" CONNECTION REFUSED"
        clientsocket.close()


while True:
    for ip in servers:
        thread.start_new_thread(server_check,(ip,))
        #print "IP = "+ip+" RTT = "+str(arr[ip]['rtt'])+" CPU = "+str(arr[ip]["cpu"])+" MEM = "+str(arr[ip]["mem"])

    time.sleep(2)
    #print arr.items()
    #for ip in arr:
    #    print "IP = "+ip+" RTT = "+str(arr[ip]['rtt'])+" CPU = "+str(arr[ip]["cpu"])+" MEM = "+str(arr[ip]["mem"])
        #print "IP = "+ip+" RTT = "+str(ip['rtt'])+" CPU = "+str(ip["cpu"])+" MEM = "+str(ip["mem"])
        #print ""
    print "----------------------------------------------"

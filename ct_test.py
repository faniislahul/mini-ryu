import thread
import httplib, urllib, random, time

url = '10.0.0.1:80'
ctr = 0
ok = 0
rt = 0
#fail_ = 0
n = ''
print "Generic test input clients/second"
n = raw_input("client : ")

def single_c():
    global ctr
    global ok
    global rt
    conn = httplib.HTTPConnection(url)
    #conn.settimeout(1)
    try:
        out = time.time()
        conn.request('GET','/generic')
        response = conn.getresponse()
        if(response.status == 200):
            ok = ok + 1
            rtt = time.time()-out
            rt = rt+rtt
        else:
            pass
        ctr = ctr + 1
        return
    except:
        ctr = ctr + 1
        return

done = 0

while done < 1000:
    r_ = random.randint(0,int(n))
    if (done + r_)<=1000:
        print "requesting "+str(r_)+" client/s"
        for i in range(0,r_):
            thread.start_new_thread(single_c,())
    else:
        r_ = 1000-done
        print "requesting "+str(r_)+" client/s"
        for i in range(0,r_):
            thread.start_new_thread(single_c,())
    time.sleep(1)
    done= done+r_
    print "RTT     = ", (rt/ok)
    print "Total   = ",ctr
    print "Success = ",ok

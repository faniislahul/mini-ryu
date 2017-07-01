import thread
import httplib, urllib, random, time

url = '10.0.0.1:80'
ctr = 0
ok = 0
#fail_ = 0

def single_c():
    global ctr
    global ok
    conn = httplib.HTTPConnection(url)
    #conn.settimeout(1)
    try:
        conn.request('GET','/')
        response = conn.getresponse()
        if(response.status == 200):
            ok = ok + 1
        else:
        #    fail_ = fail_ + 1
            pass
        ctr = ctr + 1
        return
    except:
        ctr = ctr + 1
        #fail_ = fail_ + 1
        return

def 


while 1:
    r_ = random.randint(0,10)
    print "requesting "+str(r_)+" client/s"
    for i in range(0,r_):
        thread.start_new_thread(single_c,())
    time.sleep(1)
    print "Total   = ",ctr
    print "Success = ",ok
    #print "Failed  = ",fail_

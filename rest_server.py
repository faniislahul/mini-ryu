from flask import Flask
import json
from flask import request
import psutil
import csv
import datetime

#inisialisasi apps
app = Flask(__name__)
clc = 0
#nm = datetime.datetime.now()
res = open("result/control.csv", "wb")
writer = csv.writer(res, delimiter=',')

#controller checking handler

@app.route('/control', methods = ['POST'])
def control():
#    global res
    global writer
    global clc
    seq = request.form['seq']
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory().percent
    msg = json.dumps({"cpu" : cpu,"mem" : mem, "seq" : seq, "clc" : clc})
    line = [datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),seq,mem,cpu,clc]
#    print line
    writer.writerow(line)
    return msg

#client testing handler

@app.route('/generic', methods = ['GET'])
def generic():
    global clc
    f = open("dataset/200KB", "r")
    data = f.read()
    g = open("dataset/100KB", "r")
    data1 = g.read()
    h = open("dataset/50KB", "r")
    data2 = h.read()
    clc = clc+1
    ok = "OK 200"
    return ok

@app.route('/load/sm', methods = ['GET'])
def small():
    global clc
    f = open("dataset/2MB", "r")
    data = f.read()
    clc = clc+1
    ok = "OK 200"
    return ok

@app.route('/load/md', methods = ['GET'])
def medium():
    global clc
    f = open("dataset/5MB", "r")
    data = f.read()
    clc = clc+1
    ok = "OK 200"
    return ok

@app.route('/load/lg', methods = ['GET'])
def large():
    global clc
    f = open("dataset/10MB")
    data = f.read()
    clc = clc+1
    ok = "OK 200"
    return ok


#run an app
app.run(debug=True,host='0.0.0.0', port=80)

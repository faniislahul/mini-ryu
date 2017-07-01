from flask import Flask
import json
from flask import request
import psutil

#inisialisasi apps
app = Flask(__name__)
clc = 0


@app.route('/control', methods = ['POST'])
def control():
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory().percent
    msg = json.dumps({"cpu" : cpu,"mem" : mem})
    return msg

@app.route('/', methods = ['GET'])
def index():
    text = "Velkomen"

    return text

@app.route('/postman', methods = ['POST'])
def index():
    global clc
    data = request.form['data']
    ok = "200 OK"
    clc++
    return ok



#run an app
app.run(debug=True,host='0.0.0.0', port=80)

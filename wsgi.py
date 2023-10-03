from gevent import monkey
monkey.patch_all()

import os
from gevent.pywsgi import WSGIServer
from app import app

http_server = WSGIServer(('0.0.0.0', 5000), app, certfile="SSLcertificate.crt", keyfile="SSLprivatekey.key")
http_server.serve_forever()
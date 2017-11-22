#!/bin/env python

import SocketServer
import BaseHTTPServer
import SimpleHTTPServer
import sys, os

class ThreadingSimpleServer(SocketServer.ThreadingMixIn,
                   BaseHTTPServer.HTTPServer):
    pass

if sys.argv[1:]:
    port = int(sys.argv[1])
else:
    port = 8000

FOLDER_TO_SERVE="."
os.chdir(FOLDER_TO_SERVE)
#port = int(sys.argv[-1])
#serverIP = socket.gethostbyname(socket.gethostname())

server = ThreadingSimpleServer(('', port), SimpleHTTPServer.SimpleHTTPRequestHandler)
try:
    while 1:
        sys.stdout.flush()
        server.handle_request()
except KeyboardInterrupt:
    print "Finished"

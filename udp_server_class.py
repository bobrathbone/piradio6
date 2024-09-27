#!/usr/bin/env python3
#       
# Raspberry Pi TCPIP server class
# $Id: udp_server_class.py,v 1.7 2024/08/31 16:02:13 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This program uses the Python socket server
# See https://docs.python.org/2/library/socketserver.html 
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
# The authors shall not be liable for any loss or damage however caused.
#
# This class can be tested with the remote_control.py program.
# sudo ./remote_control.py send TEST
#
# When running it can be checked to see if it is listening on port 5100
# netstat -an | grep 5100
# udp        0      0 0.0.0.0:5100            0.0.0.0:*

import socket
import sys
import os
import time
import threading
import socketserver
import pdb
from log_class import Log

log = Log()

PORT = 5100
HOST = '0.0.0.0'
callback = None
client_data = ""

# Class to handle the data requests
class RequestHandler(socketserver.BaseRequestHandler):

    # Handle the data request
    def handle(self):
        global  callback
        global  client_data
        socket = None
        try:
            client_data = self.request[0].strip()
            client_data = client_data.decode("utf-8")
            socket = self.request[1]
            log.message("UDP Server received: " + client_data, Log.DEBUG)
            reply = callback()  # Call the get data routine
            reply = reply.encode()
            socket.sendto(reply, self.client_address)
        except Exception as e:
            log.message("UDP RequestHandler " + str(e), Log.ERROR)
            reply = "NOTOK".encode()
            socket.sendto(reply, self.client_address)
        return

    # Handle client disconnect
    def finish(self):
        log.message("UDP server client disconnect", Log.DEBUG)

    # Handle time out
    def handle_timeout(self):
        log.message("UDP server server timeout", Log.DEBUG)

class UDPServer(socketserver.ThreadingMixIn, socketserver.UDPServer):
    pass # We will override class methods
    port = PORT
    host = HOST

    log.init('radio')
    pid = os.getpid()
    log.message("Initialising UDP server, pid %d" % pid, log.INFO)

    # Listen for incomming connections
    def listen(self,server, mycallback):
        global  callback
        callback = mycallback  # Set up the callback

        # Start a thread with the server
        server_thread = threading.Thread(target=server.serve_forever)
        # Exit the server thread when the main thread terminates
        server_thread.daemon = True
        server_thread.name = 'remote'
        server_thread.timeout = 2 
        server_thread.start()
        self._stop_event = threading.Event()
        msg = "UDP listen:" + server_thread.name + " " + str(self.host) \
                 + " port " + str(self.port)
        log.message(msg, Log.INFO)

    def stop(self):
        self._stop_event.set() 

    def getServerAddress(self):
        return (self.host,self.port)

    # This routine call from the radio class to retrive the
    # the remote control data 
    def getData(self):
        global client_data
        data = client_data
        client_data = ''
        return data

# Test UDP server class
if __name__ == "__main__":
    
    server = None

    # Call back routine to get data event
    def callback():
        global server
        print("Data =", server.getData())
        return 

    server = UDPServer((HOST, PORT), RequestHandler)
    try:
        print ("Starting UDP server on port " + str(PORT))
        server.serve_forever()

        server.listen(server,callback)

    except KeyboardInterrupt:
        server.shutdown()
        server.server_close()
        msg = "Exiting remote listener"
        print(msg)
        log.message(msg, Log.INFO)
        sys.exit(0)

    finally:
        server.server_close()

# End of class
# set tabstop=4 shiftwidth=4 expandtab
# retab


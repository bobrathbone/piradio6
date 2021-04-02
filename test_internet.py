#!/usr/bin/python3

import socket

def checkInternet(host="google.com", port=80, timeout=5):
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error as ex:
        print(ex)
        return False

print ("Connected", checkInternet())

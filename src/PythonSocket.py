import socket
from time import sleep
from globals import *

def send_data(array):
    """
    Send a given array to a socket as a string.

    @param array: 2-D array.
    """
    s = socket.socket()  
    ip = socket.gethostbyname(socket.gethostname())

    # connect to the server on local computer 
    s.connect((ip, PORT))

    for i in range(len(array)):
        for j in range(len(array[i])):
            s.send((str(array[i][j]) + ",").encode())

    s.close()

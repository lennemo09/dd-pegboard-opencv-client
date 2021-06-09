import socket
from time import sleep

def sendData():
    s = socket.socket()  
    ip = socket.gethostbyname(socket.gethostname())                  
    # connect to the server on local computer 
    s.connect((ip, 8080))
    for i in range(len(arrayToSend)):
        for j in range(len(arrayToSend[i])):
            s.send((str(arrayToSend[i][j]) + ",").encode())
    s.close()

arrayToSend = [(1,2),(3,4),(5,6)]
sendData()

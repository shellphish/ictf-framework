import socket
import struct

#create and connect to the socket
def getSocket(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, int(port)))
    return s

def recvMessage(s):
    l = s.recv(4)
    L = struct.unpack('<I',l)[0]
    #print L
    data = ''
    while (len(data)<L):
        data += s.recv(L)
    return data 

def sendMessage(s,mess):
    l = len(mess)
    byteLength = struct.pack('<I', l)
    s.sendall(byteLength)
    s.sendall(mess)

def closeSocket(s):
    s.close()



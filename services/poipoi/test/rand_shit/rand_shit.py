from service import *
import sys
import os

host = '192.168.48.168'
port = '3335'
ok = "ACK_OK"

s = getSocket(host, port)

#registration
def reg():
    global name
    global passwd

    data = recvMessage(s)#receive username
    # print data
    input  = name
    sendMessage(s,input) #send username
    data = recvMessage(s) #receive pwd
    # print data
    input  = passwd
    sendMessage(s,input) #send pwd
    data = recvMessage(s) #receive status
    if (data!=ok): #error
        # print data
        return -1
    else:
        data = recvMessage(s) #receive confirm
        id = data.split('<',2)[1]
        name = id.split('>',1)[0]

        # print data
        return 0

#login
def login():
    global name
    global passwd

    data = recvMessage(s) # receive username
    # print data
    input = name
    sendMessage(s,input) #send username
    data = recvMessage(s) #receive pwd
    # print data
    input = passwd
    sendMessage(s,input) #send pwd
    data = recvMessage(s) # receive status
    if (data!=ok):
        # print data
        return -1
    else:
        data = recvMessage(s) #receive confirm
        # print data
        return 0

#help
def help():
    data = recvMessage(s) # receive what help you want?
    # print data
    input = raw_input('')
    sendMessage(s,input) #send command
    data = recvMessage(s) # receive status
    if (data!=ok):
        # print data
        return -1
    else:
        data = recvMessage(s) #receive help page
        # print data
        return 0

#exit
def exit():
    data = recvMessage(s) #receive menu exit
    # print data
    input  = raw_input('')
    sendMessage(s,input) #send command
    if (input == 'y' or input == 'Y'):
        return -1
    return 0

#insert_POI
def insert_poi():
    global lat
    global lon

    data = recvMessage(s) #receive login status
    if (data != ok):
        # print data
        return -1
    else:
        data = recvMessage(s) #receive insert lat
        # print data
        input  = str(lat)
        sendMessage(s,input) #send lat
        data = recvMessage(s) #receive insert long
        # print data
        input  = str(lon)
        sendMessage(s,input) #send long
        data = recvMessage(s) #receive insert name
        # print data
        input  = "maiale se sfoa;"
        sendMessage(s,input) #send name
        data = recvMessage(s) #receive status
        if (data != ok):
            # print data
            return -1
        else:
            data = recvMessage(s) #receive confirm
            # print data
            return 0

#view POI
def view_poi():
    data = recvMessage(s) #receive login status
    if (data != ok):
        # print data
        return -1
    else:
        data = recvMessage(s) #receive list POI
        # print data
        return 0



name = sys.argv[1]
passwd = sys.argv[2]
lat = -90
lon = -90

    #os.system('clear')
data = recvMessage(s)#receive menu
# print data
input  = 'r'
sendMessage(s,input)#send command
data = recvMessage(s)#receive status

if (data!=ok):#error
    # print data
    sys.exit -1
if reg():
    sys.exit -1

data = recvMessage(s)#receive menu
# print data
input  = 'l'
sendMessage(s,input)#send command
data = recvMessage(s)#receive status
if (data!=ok):#error
    # print data
    sys.exit -1

if login():
    sys.exit -1


for i in range(1, 2):
    for j in range(1, 10):
        data = recvMessage(s)#receive menu
        # print data
        input  = 'a'
        sendMessage(s,input)#send command
        data = recvMessage(s)#receive status
        if (data!=ok):#error
            # print data
            sys.exit -1

        lat += 1
        lon += 1
        if insert_poi():
            sys.exit -1

    data = recvMessage(s)#receive menu
    # print data
    input  = 'g'
    sendMessage(s,input)#send command
    data = recvMessage(s)#receive status
    if (data!=ok):#error
        # print data
        sys.exit -1

    if view_poi():
        sys.exit -1


print "close"
closeSocket(s)

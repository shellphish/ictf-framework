import sys
import os
import random
import math

XXXSHAREDXXX

def checkflag(s):
    sendMessage(s,'g')
    data = recvMessage(s) #receive ack
    data = recvMessage(s) #receive login status
    if (data != ok):
        return -1
    else:
        if (DEBUG):
            print ('logged')
        data = recvMessage(s) #receive list POI (in this case just one)
        if (DEBUG):
            print data
        flag = data.split(':')[2]
        flag = flag.split()[0]
        if (DEBUG):
            print flag
        return flag

class GetFlag():

    def __init__(self):
        self.error = 0
        self.error_msg = ''
        self.flag = ''

    def execute(self, ip, port, flag_id, token):
        try:
            s = getSocket(ip, port)
        except Exception as e:
            self.flag = ''
            self.error = -1
            self.error_msg = "connection refused"
            return

        try:
            data = recvMessage(s) #receive main menu
            if (DEBUG):
                print data

            login(s, flag_id, token) # login
            data = recvMessage(s) #receive main menu
            if (DEBUG):
                print data
            self.flag = checkflag(s)
            data = recvMessage(s) #receive main menu

            exit(s, 'y') #exit
            closeSocket(s)
        except Exception as e:
            self.flag = ''
            self.error = 1
            self.error_msg = str(e)

    def result(self):
        return {'FLAG' : self.flag,
                'ERROR' : self.error,
                'ERROR_MSG' : self.error_msg
                }

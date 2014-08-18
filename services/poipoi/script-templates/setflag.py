import sys
import os
import random
import math

XXXSHAREDXXX

class SetFlag():
    def __init__(self):
        self.flag_id = ''
        self.token = ''
        self.error = 0
        self.error_msg = ''

    def execute(self,ip,port, flag):
        if (DEBUG):
            print flag
        a = ['0','1','2','3','4','5','6','7','8','9','A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']
        nameLength = random.randint(5,20)
        pwdLength = random.randint(5,30)
        name = ''
        pwd = ''
        for i in range(1,nameLength):
            name += a[random.randint(0,len(a)-1)]
        for i in range(1,pwdLength):
            pwd += a[random.randint(0,len(a)-1)]

        if (DEBUG):
            print name
        if (DEBUG):
            print pwd
        try:
            s = getSocket(ip, port)
        except Exception as e:
            self.token = ''
            self.flag_id = ''
            self.error = -1
            self.error_msg = "connection refused"
            return

        try:
            data = recvMessage(s) #receive main menu
            if (DEBUG):
                print data

            self.flag_id = reg(s,name,pwd) #register
            #print self.flag_id
            self.token = pwd

            data = recvMessage(s)# receive main menu

            login(s,self.flag_id, pwd) # login

            data = recvMessage(s)# receive main menu

            long = math.ceil(random.uniform(-180, 180)*10000000)/10000000
            lat = math.ceil(random.uniform(-90, 90)*10000000)/10000000
            if (DEBUG):
                print long
            if (DEBUG):
                print lat

            insert_poi(s,str(long), str(lat), flag) #insert POI

            data = recvMessage(s)#receive menu

            exit(s, 'y') #exit
            if (DEBUG):
                print (self.flag_id)
            closeSocket(s)
        except Exception as e:
            self.token = ''
            self.flag_id = ''
            self.error = 1
            self.error_msg = str(e)

    def result(self):
        return {'FLAG_ID' : self.flag_id,
                'TOKEN' : self.token,
                'ERROR' : self.error,
                'ERROR_MSG' : self.error_msg
                }

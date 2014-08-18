import sys
import os
import random
import math

XXXSHAREDXXX

class Benign():

    def __init__(self):
        self.error = 0
        self.error_msg = ''
        self.flag_id = ''
        self.token = ''


    def makeCredentials(self):
        if (DEBUG):
            print "function makeCredential()"
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
        return name,pwd


    def reg_addPOI_ok(self, s):
        if (DEBUG):
            print ("Benign traffic: branch reg_addPOI_ok")
        cr = self.makeCredentials()
        name = cr[0]
        self.token = cr[1]
        self.flag_id = reg(s,name,self.token) #register
        if (DEBUG):
            print self.flag_id
        data = recvMessage(s)# receive main menu
        login(s,self.flag_id, self.token) # login
        data = recvMessage(s)# receive main menu
        long = math.ceil(random.uniform(-180, 180)*10000000)/10000000
        lat = math.ceil(random.uniform(-90, 90)*10000000)/10000000
        flag = str(random.randint(1,1000))
        insert_poi(s,str(long), str(lat), flag) #insert POI
        if (DEBUG):
            print "inserted"
        data = recvMessage(s)#receive menu
        exit(s, 'y') #exit
        if (DEBUG):
            print ("Benign traffic: registered, logged in and added POI successfully")

    def log_getPOI(self, s, flag_id, token):
        if (DEBUG):
            print ("Benign traffic: branch log_getPOI")
        if (flag_id == '' or token == ''):
            cr = self.makeCredentials()
            flag_id = cr[0]
            token = cr[1]
        res = login(s,flag_id, token) # login
        if (res!=0):
            if (DEBUG):
                print ("Benign traffic: login refused")
            return -1
        data = recvMessage(s)# receive main menu
        view_poi(s)
        data = recvMessage(s)# receive main menu
        exit(s, 'y') #exit
        if (DEBUG):
            print ("Benign traffic: logged in and viewed POI successfully")
        return 0

    def login_error(self,s):
        if (DEBUG):
            print ("Benign traffic: branch login_error")
        cr = self.makeCredentials()
        name = cr[0]
        pwd = cr[1]
        res = login(s,name, pwd) # login
        if (res!=0):
            if (DEBUG):
                print ("Benign traffic: login refused")
            return -1
        data = recvMessage(s)# receive main menu
        exit(s, 'y') #exit
        if (DEBUG):
            print ("Benign traffic: logged in successfully")
        return 0


    def help_ok(self, s):
        if (DEBUG):
            print ("Benign traffic: branch help_ok")
        res = help(s,'r')
        if (res!=0):
            if (DEBUG):
                print ("Benign traffic: help error")
            return -1
        data = recvMessage(s) # receive main imenu
        exit(s, 'y') #exit
        if (DEBUG):
            print ("Benign traffic: help page viewd successfully")
        return 0



    def execute(self,ip,port,flag_id="empty", token="empty"):
        self.flag_id = flag_id
        self.token = token
        if (DEBUG):
            print (flag_id, token)
        branch = random.randint(0, 3)
        if (DEBUG):
            print ("branch", branch)
        try:
            s = getSocket(ip, port)
        except Exception as e:
            self.flag_id = ''
            self.token = ''
            self.error = -1
            self.error_msg = "connection refused"
            return

        try:
            data = recvMessage(s) #receive main menu
            if (DEBUG):
                print data
            if (branch==0):
                self.reg_addPOI_ok(s)
            elif (branch==1):
                self.log_getPOI(s, flag_id, token)
            elif (branch==2):
                self.help_ok(s)
            elif (branch==3):
                self.login_error(s)
            if (DEBUG):
                print branch
            closeSocket(s)
        except Exception as e:
            self.flag_id = ''
            self.token = ''
            self.error = 1
            self.error_msg = str(e)

    def result(self):
        return {'FLAG_ID' : self.flag_id,
                'TOKEN' : self.token,
                'ERROR' : self.error,
                'ERROR_MSG' : self.error_msg
                }

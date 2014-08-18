# check flag example

class GetFlag():

    DEBUG = False

    def recv_until_colon(self, s):
        ret = ""
        while True:
            data = s.recv(1)
            if len(data) == 0:
                raise Exception("Socket is broken. socket.recv() returns empty string.")
            ret += data
            if ret[len(ret) - 1 : ] == ':':
                break
        return ret

    def recv_until_linebreak(self, s):
        ret = ""
        while True:
            data = s.recv(1)
            if len(data) == 0:
                raise Exception("Socket is broken. socket.recv() returns empty string.")
            ret += data
            if ret[len(ret) - 1 : ] == '\n':
                break
        return ret

    def recv_until_main_menu(self, s):
        ret = ""
        while True:
            data = s.recv(1)
            if len(data) == 0:
                raise Exception("Socket is broken. socket.recv() returns empty string.")
            ret += data
            if ret[len(ret) - 10 : ] == ' ========\n':
                break
        return ret

    # We generate a username according to current flag_id.
    def gen_username(self, flag_id):
        LEGITIMATE_USERNAME = ["LetMeFly","TryThis","CatLovers","test00001","fanqiang","YouMotherFxxxers","realcompanyltd","y4nSh0shit4shvi1i"]
        import md5
        m = md5.new()
        m.update(flag_id)
        digest = m.hexdigest()
        index = int(digest, 16) % len(LEGITIMATE_USERNAME)
        return LEGITIMATE_USERNAME[index] + digest[2 : 5]

    # The password is generated according to current username 
    def gen_password(self, username):
        LEGITIMATE_PASSWORD = ["McDonalds","pleasedontcr4sh","123456","13133211","Op0PoPop", "poiu;lkj"]
        import md5
        m = md5.new()
        m.update(username)
        digest = m.hexdigest()
        index = int(digest, 16) % len(LEGITIMATE_PASSWORD)
        return LEGITIMATE_PASSWORD[index] + digest[4 : 7]

    def client_register(self, s, username, password):
        if self.DEBUG: print "client_register(%s, %s)" % (username, password)
        self.recv_until_colon(s)
        s.send("1\n") # Register
        self.recv_until_colon(s)
        s.send(username + "\n") # Username
        self.recv_until_colon(s)
        s.send(password + "\n") # Password
        self.recv_until_colon(s)
        s.send(password + "\n") # Repeat password
        data = self.recv_until_linebreak(s)
        if self.DEBUG: print data
        if data.find("succeeded") != -1:
            # Registration succeeded
            return True
        else:
            # Registration failed, either duplicated name, or it just doesn't work
            return False
    
    def client_login(self, s, username, password):
        if self.DEBUG: print "client_login(%s, %s)" % (username, password)
        self.recv_until_colon(s)
        s.send("2\n") # Login
        self.recv_until_colon(s)
        s.send(username + "\n") # Username
        self.recv_until_colon(s)
        s.send(password + "\n") # Password
        data = self.recv_until_linebreak(s)
        if self.DEBUG: print data
        if data.find("Successfully") != -1:
            # Logged-in successfully
            return True
        else:
            return False

    def client_list_driller(self, s, driller_name):
        if self.DEBUG: print "client_list_driller(%s)" % (driller_name)
        self.recv_until_colon(s)
        s.send("4\n") # List drillers (admin)
        self.recv_until_colon(s)
        s.send(driller_name + "\n")
        data = self.recv_until_main_menu(s)
        if self.DEBUG: print data
        import re
        p = re.compile(r'Name: (\S*)\nLocation: ([\S ]*)\n')
        tuples = p.findall(data)
        flag = ""
        if len(tuples) > 0:
            flag = tuples[0][1]
        return flag

    def do_getflag(self, s, flag_id, token):
        if self.DEBUG: print 'Getting flag..'
        # Username is decided by flag_id
        username = self.gen_username(flag_id)
        # Password is decided by username :)
        password = self.gen_password(username)
        # Skip the first colon after "Statistics"
        self.recv_until_colon(s)
        # Try to register
        ret = self.client_register(s, username, password)
        # Try to login
        ret = self.client_login(s, username, password)
        if not ret:
            if self.DEBUG: print "Login failed. Is service down?"
            # Service is down?
            return
        # List the drillers
        flag = self.client_list_driller(s, token)
        return flag

    def execute(self, ip, port, flag_id, token):

        from socket import socket

        flag = ''
        error = 0
        error_msg = ''
        try:
            s = socket()
            s.connect((ip, port))
            flag = self.do_getflag(s, flag_id, token)
        except Exception as e:
            error = 42
            error_msg = str(e)

        self.flag = flag
        self.error = error
        self.error_msg = error_msg

    def result(self):
        return {'FLAG' : self.flag,
                'ERROR' : self.error,
                'ERROR_MSG' : self.error_msg,
               }

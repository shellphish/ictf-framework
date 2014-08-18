'''
This is the setflag script for service "driller".
flag_id is the spot's name, and driller's name is the flag.
'''

class SetFlag():

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
    
    def client_create_spot(self, s, spot_name):
        if self.DEBUG: print "client_create_spot()"
        data = self.recv_until_colon(s)
        if self.DEBUG: print data
        s.send("1\n") # Add a spot
        data = self.recv_until_colon(s)
        if self.DEBUG: print data
        s.send(spot_name + "\n") # name for this spot
        self.recv_until_colon(s)
        data = self.recv_until_colon(s)
        if self.DEBUG: print data
        # Extract all spot location IDs
        import re
        import random
        p = re.compile(r'(\d+).\s[\S]+')
        ids = p.findall(data)
        r = random.Random()
        option = ids[r.randint(0, len(ids) - 1)]
        s.send(option + "\n") # country/area for this spot
        data = self.recv_until_linebreak(s)
        if self.DEBUG: print data
        # Done!
        return True
    
    def client_create_driller(self, s, spot_name, driller_name, location):
        if self.DEBUG: print "client_create_driller()"
        self.recv_until_colon(s)
        s.send("3\n") # Add a driller
        self.recv_until_colon(s)
        data = self.recv_until_colon(s)
        if self.DEBUG: print data
        import re
        p = re.compile(r'^(\d+).\s([ \t\S]+)$', re.MULTILINE)
        spots = p.findall(data)
        try:
            option_index = [y for x,y in spots].index(spot_name)
        except:
            if self.DEBUG:
                print "Something is wrong when creating a driller..."
                print "Spots: %s" % spots
            return
        option = spots[option_index][0]
        s.send(option + "\n") # Spot index
        self.recv_until_colon(s)
        s.send(driller_name + "\n") # Driller name
        self.recv_until_colon(s)
        s.send(location + "\n") # Driller location
        self.recv_until_linebreak(s)
        # We are done!
        return True

    def send_recv_msg(self, s, msg):
        s.send(msg + '\n')
        ans = s.recv(128).strip()
        return ans

    def get_msg(self, s):
        msg = s.recv(128).strip()
        return msg

    def do_setflag(self, s, flag_id, token, flag):
        if self.DEBUG: print 'Setting flag..'
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
        # Create the spot
        self.client_create_spot(s, flag_id)
        # Create the driller
        self.client_create_driller(s, flag_id, token, flag)
        # We are done!
        # Be a good guy :)
        print self.recv_until_colon(s)

    def execute(self, ip, port, flag):

        def get_random_flag_id():
            import random
            import string
            username = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(10))
            return '%s' % username

        def get_random_token():
            import random
            import string
            return ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(16))

        from socket import socket

        flag_id = get_random_flag_id()
        token = get_random_token()
        error = 0
        error_msg = ''
        try:
            s = socket()
            s.connect((ip, port))
            self.do_setflag(s, flag_id, token, flag)
        except Exception as e:
            error = 42
            error_msg = str(e)

        self.flag_id = flag_id
        self.token = token
        self.error = error
        self.error_msg = error_msg


    def result(self):
        return {'FLAG_ID' : self.flag_id,
                'TOKEN' : self.token,
                'ERROR' : self.error,
                'ERROR_MSG' : self.error_msg,
               }

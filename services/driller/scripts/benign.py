# benign traffic example
from socket import socket

class Benign():

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
                raise Exception()
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
    def gen_username(self):
        import random
        import string
        username_type = random.randint(1, 7)
        username_length = random.randint(4, 20)
        charsets = ""
        if username_type & 1:
            charsets += string.ascii_lowercase
        if username_type & 2:
            charsets += string.ascii_uppercase
        if username_type & 4:
            charsets += string.digits
        username = "".join(random.choice(charsets) for x in range(username_length))
        return username
        
    # The password is generated according to current username 
    def gen_password(self, username):
        import md5
        m = md5.new()
        m.update(username)
        digest = int(m.hexdigest(), 16)
        if digest & 8:
            m1 = md5.new()
            m1.update("y0ud0ntk0nwwh4t'shere" + username + "c0me0nGuys!")
            return m.hexdigest()[8 : 16]
        else:
            m1 = md5.new()
            m1.update(username + "xxxxxxxx")
            return m.hexdigest()[0 : 14].upper()

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

    def client_list_spot(self, s):
        if self.DEBUG: print "client_list_spot()"
        data = self.recv_until_colon(s)
        if self.DEBUG: print data
        s.send("2\n") # List spots
        data = self.recv_until_colon(s)
        if self.DEBUG: print data
        import string
        import random
        REGEX = ["a", "b", "c", "test", "", r"\s\S+", r"\d+", "".join(random.choice(string.ascii_lowercase + string.ascii_uppercase) for x in range(random.randint(4, 9)))]
        REGEX_SUFFIX = [r"\s*", "", r"\S*", r"[^\n\s]{0, 5}"]
        regex = random.choice(REGEX) + random.choice(REGEX_SUFFIX)
        if self.DEBUG: print "regex = " + regex
        s.send(regex + "\n") # name for this spot
        data = self.recv_until_main_menu(s)
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

    def client_list_driller(self, s):
        if self.DEBUG: print "client_list_driller()"
        data = self.recv_until_colon(s)
        if self.DEBUG: print data
        s.send("4\n") # List spots
        data = self.recv_until_colon(s)
        if self.DEBUG: print data
        import string
        import random
        REGEX = ["a", "b", "c", "test", "", r"\s\S+", r"\d+", "".join(random.choice(string.ascii_lowercase + string.ascii_uppercase) for x in range(random.randint(4, 9)))]
        REGEX_SUFFIX = [r"\s*", "", r"\S*", r"[^\n\s]{0, 5}"]
        regex = random.choice(REGEX) + random.choice(REGEX_SUFFIX)
        if self.DEBUG: print "regex = " + regex
        s.send(regex + "\n") # name for this spot
        data = self.recv_until_main_menu(s)
        if self.DEBUG: print data
        # Done!
        return True

    def do_benign(self, s):
        if self.DEBUG: print 'Benign..'
         # Username is decided by flag_id
        username = self.gen_username()
        # Password is decided by username :)
        password = self.gen_password(username)
        # Skip the first colon after "Statistics"
        self.recv_until_colon(s)

        import random

        if random.randint(0, 8) == 4:
            # A failed login :)
            ret = self.client_login(s, username[ : len(username) - 1], self.gen_password(username + "a"))
        else:
            # Try register
            ret = self.client_register(s, username, password)
            # Try login
            ret = self.client_login(s, username, password)
            if not ret:
                if self.DEBUG: print "Login failed. Is service down?"
                # Service is down?
                return
            
            while True:
                if random.randint(0, 6) < 3:
                    import string
                    # Create a spot
                    spot_name_length = random.randint(10, 15)
                    spot_name = "".join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for x in range(spot_name_length))
                    self.client_create_spot(s, spot_name)

                    if random.randint(0, 5) < 3:
                        # Create a driller
                        driller_name_length = random.randint(4, 18)
                        driller_name = "".join(random.choice(string.ascii_uppercase + string.digits) for x in range(driller_name_length))
                        location_length = random.randint(4, 12)
                        location = "".join(random.choice(string.ascii_uppercase + string.digits) for x in range(location_length))
                        self.client_create_driller(s, spot_name, driller_name, location)
                    else:
                        # Create another spot
                        spot_name_length = random.randint(10, 15)
                        spot_name = "".join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for x in range(spot_name_length))
                        self.client_create_spot(s, spot_name)
                else:
                    if random.randint(0, 1) == 0:
                        # Search for a spot
                        self.client_list_driller(s)
                    else:
                        # Search for a driller
                        self.client_list_spot(s)

                if random.randint(0, 8) == 4:
                    # Exit loop
                    break
        # We are done!
        return ""

    def execute(self, ip, port, flag_id, token):
        # This example will ignore the flag_id and token. If you want,
        # you can actually use them to "re-use" a previously created
        # flag_id/token/flag entry.
        error = 0
        error_msg = ''
        try:
            s = socket()
            s.connect((ip, port))
            ans = self.do_benign(s)
        except Exception as e:
            error = 42
            error_msg = str(e)

        self.flag_id = ''
        self.token = ''
        self.error = error
        self.error_msg = error_msg

    def result(self):
        return {'FLAG_ID' : self.flag_id,
                'TOKEN' : self.token,
                'ERROR' : self.error,
                'ERROR_MSG' : self.error_msg,
               }

# check flag example

class GetFlag():

    def execute(self, ip, port, flag_id, token):

        #from socket import socket
        from telnetlib import Telnet

        def send_msg(t, msg):
            t.write(msg+'\n')

        def read_until_prompt(t):
            ans =t.read_until('getflag: ')
            return ans

        def do_checkflag(t, flag_id, token):
            send_msg(t, '3')
            send_msg(t, flag_id)
            send_msg(t, token)
            ans = read_until_prompt(t)
            flag = ans.split(' ')[-1].split()
            return flag
    

        flag = ''
        error = 0
        error_msg = ''
        try:
            t = Telnet(ip,port)
            flag = do_checkflag(t, flag_id, token)[0]

            if flag == "getflag_auth_fail":
                error = 1 #up but not functional
                error_msg = flag
            elif flag == "no_entry_exists":
                error = 1 # up but not functional
                error_msg = flag
            t.close()   
        except Exception as e:
            error = -1
            error_msg = str(e)

        self.flag = flag
        self.error = error
        self.error_msg = error_msg

    def result(self):
        return {'FLAG' : self.flag,
                'ERROR' : self.error,
                'ERROR_MSG' : self.error_msg,
               }


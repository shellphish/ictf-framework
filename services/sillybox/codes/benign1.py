#!/usr/bin/env python

import random
import socket
import string
import struct
from time import sleep

def generate_str(length):
    POSSIBILITIES = string.ascii_uppercase + string.digits + string.ascii_lowercase
    return ''.join(random.choice(POSSIBILITIES) for x in range(length))


# From reader_of_len
# code_1 (dword read length) code_2 (filename)
code_1 = b'\xE8\x00\x00\x00\x00\x5F\x8D\x5F\x4B\x31\xC9\xB8\x05\x00\x00\x00\x65\xFF\x15\x10\x00\x00\x00\xBB\x01\x00\x00\x00\x89\xC1\x31\xD2\xBE'
code_2 = b'\xB8\xBB\x00\x00\x00\x65\xFF\x15\x10\x00\x00\x00\x89\xCB\xB8\x06\x00\x00\x00\x65\xFF\x15\x10\x00\x00\x00\xBB\x00\x00\x00\x00\xB8\xFC\x00\x00\x00\x65\xFF\x15\x10\x00\x00\x00'


def sendcode(ip, port, pwd, code):
    pkt = bytearray()
    pkt.append(chr(len(pwd)))
    pkt.extend(pwd)
    pkt.extend(code)
    s = socket.create_connection((ip,port))
    s.sendall(pkt)
    sleep(0.2)
    s.shutdown(socket.SHUT_WR)
    data = s.recv(1024)
    s.close()
    return data

class Benign():

    def execute(self, ip, port, flag_id, token):
        error = 0
        error_msg = ''


        # Tries to open a random file name
        # Must not return any output

        flag_id = generate_str(length=1+random.randrange(120))
        token = generate_str(length=1+random.randrange(40))
        fixed_read_len = 16 + random.randrange(180)

        try:
            code = bytearray()
            code.extend(code_1)
            code.extend(struct.pack("<L", fixed_read_len))
            code.extend(code_2)
            code.extend(flag_id)
            code.append(0)
            flag = sendcode(ip, port, token, code)
        except Exception as e:
            error = 42
            error_msg = str(e)

        self.error = error
        self.error_msg = error_msg

    def result(self):
        return {'FLAG_ID' : '',
                'TOKEN' : '',
                'ERROR' : self.error,
                'ERROR_MSG' : self.error_msg,
               }

if __name__ == "__main__":
    import sys
    b = Benign()
    b.execute("127.0.0.1",4669,'','')
    print repr(b.result())

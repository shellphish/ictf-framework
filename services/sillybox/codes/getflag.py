#!/usr/bin/env python

import random
import socket
import struct
from time import sleep


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

class GetFlag():

    def execute(self, ip, port, flag_id, token):
        flag = ''
        error = 0
        error_msg = ''

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

        self.flag = flag
        self.error = error
        self.error_msg = error_msg

    def result(self):
        return {'FLAG' : self.flag,
                'ERROR' : self.error,
                'ERROR_MSG' : self.error_msg,
               }

if __name__ == "__main__":
    import sys
    gf = GetFlag()
    gf.execute("127.0.0.1",4669,sys.argv[1],sys.argv[2])
    print repr(gf.result())

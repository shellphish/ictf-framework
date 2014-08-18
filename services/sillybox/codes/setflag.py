#!/usr/bin/env python

import random
import socket
import string
import struct
from time import sleep


# from writer
# wo_code_1 | (dword) content len | wo_code_2 | filename length 50 | \x0 | content
wo_code_1 = b'\xE8\x00\x00\x00\x00\x5F\x8D\x5F\x50\xB9\xC1\x00\x00\x00\xBA\x80\x01\x00\x00\xB8\x05\x00\x00\x00\x65\xFF\x15\x10\x00\x00\x00\x89\xC3\x8D\x8F\x83\x00\x00\x00\xBA'
wo_code_2 = b'\xB8\x04\x00\x00\x00\x65\xFF\x15\x10\x00\x00\x00\xB8\x06\x00\x00\x00\x65\xFF\x15\x10\x00\x00\x00\xBB\x00\x00\x00\x00\xB8\xFC\x00\x00\x00\x65\xFF\x15\x10\x00\x00\x00'

# from writer_and_reader
# (same-ish) 
wr_code_1 = b'\xE8\x00\x00\x00\x00\x5F\x8D\x9F\x8F\x00\x00\x00\xB9\xC1\x00\x00\x00\xBA\x80\x01\x00\x00\xB8\x05\x00\x00\x00\x65\xFF\x15\x10\x00\x00\x00\x89\xC3\x8D\x8F\xC2\x00\x00\x00\xBA'
wr_code_2 = b'\xB8\x04\x00\x00\x00\x65\xFF\x15\x10\x00\x00\x00\xB8\x06\x00\x00\x00\x65\xFF\x15\x10\x00\x00\x00\x8D\x9F\x8F\x00\x00\x00\x31\xC9\xB8\x05\x00\x00\x00\x65\xFF\x15\x10\x00\x00\x00\xBB\x01\x00\x00\x00\x89\xC1\x31\xD2\xBE'
wr_code_3 = b'\xB8\xBB\x00\x00\x00\x65\xFF\x15\x10\x00\x00\x00\x89\xCB\xB8\x06\x00\x00\x00\x65\xFF\x15\x10\x00\x00\x00\xBB\x00\x00\x00\x00\xB8\xFC\x00\x00\x00\x65\xFF\x15\x10\x00\x00\x00'


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

POSSIBILITIES = string.ascii_uppercase + string.digits + string.ascii_lowercase
def generate_str(length):
    return ''.join(random.choice(POSSIBILITIES) for x in range(length))

class SetFlag():

    def execute(self, ip, port, flag):
        error = 0
        error_msg = ''

        flag_id = generate_str(length=50)
        token = generate_str(length=30)
        assert len(flag) == 16
        assert len(flag_id) == 50

        code = bytearray()
        code.extend(wo_code_1)
        code.extend(struct.pack("<L", len(flag)))
        code.extend(wo_code_2)
        code.extend(flag_id)
        code.append(0)
        code.extend(flag)

        reread = random.choice([True,False])
        if reread:
            code = bytearray()
            code.extend(wr_code_1)
            code.extend(struct.pack("<L", len(flag)))
            code.extend(wr_code_2)
            code.extend(struct.pack("<L", len(flag)))
            code.extend(wr_code_3)
            code.extend(flag_id)
            code.append(0)
            code.extend(flag)

        try:
            output = sendcode(ip, port, token, code)
            if reread and output != flag:
                error = 2
                error_msg = 'Could not read back the flag. Output: \n '+output
        except Exception as e:
            error = 42
            error_msg = str(e)

        self.error = error
        self.error_msg = error_msg
        self.flag_id = flag_id
        self.token = token

    def result(self):
        return {'FLAG_ID' : self.flag_id,
                'TOKEN' : self.token,
                'ERROR' : self.error,
                'ERROR_MSG' : self.error_msg,
               }

if __name__ == "__main__":
    import sys
    sf = SetFlag()
    sf.execute("127.0.0.1",4669,sys.argv[1])
    print repr(sf.result())

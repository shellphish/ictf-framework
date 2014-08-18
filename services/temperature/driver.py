#!/usr/bin/env python
import sys

from benign import Benign
from exploit import Exploit
from getflag import GetFlag
from setflag import SetFlag

HOST = '127.0.0.1'
PORT = int(sys.argv[1])

FLAG = 'xxxflagxxx'

print 'Setflag..'
sf = SetFlag()
sf.execute(HOST, PORT, FLAG)
res = sf.result()
print 'Result: %s' % str(res)
flag_id = res['FLAG_ID']
cookie = res['TOKEN']

print 'Exploit..'
e = Exploit()
e.execute(HOST, PORT, flag_id)
res = e.result()
print 'Result: %s' % str(res)
assert res['FLAG'] == FLAG

print 'Getflag..'
cf = GetFlag()
cf.execute(HOST, PORT, flag_id, cookie)
res = cf.result()
print 'Result: %s' % str(res)
assert res['FLAG'] == FLAG

print 'Benign..'
b = Benign()
b.execute(HOST, PORT)
res = b.result()
print 'Result: %s' % str(res)
assert res['ERROR'] == 0

# -*- coding: utf-8 -*-

class GetFlag():
  def execute(self, ip, port, flag_id, token):
    import socket
    import random
    import time
    import datetime
    
    flag = ''
    error = -1
    error_msg = ''
 
    try:
      s = socket.socket()
      s.connect((ip,port))

      msg = s.recv(1024)
      s.send("1")
      s.recv(1024)
      s.send(flag_id)
      s.recv(1024)
      s.send(token)
      msg = s.recv(1024)
      flag = msg.split('\n')[-2]
      error = 0

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

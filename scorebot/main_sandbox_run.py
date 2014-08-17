import os,sys,json,imp
from threading import Thread

# args are script_id,timeout,script_type,script_path,ip,port,args..

ERROR_ARG = (0xA000,"Sandbox: Not enough arguments passed to SandboxRun.")
ERROR_ARG_PARSE = (0xA001,"Sandbox: Error parsing arguments.")
ERROR_TIMEOUT = (0xA002,"Sandbox: Script timeout.")
ERROR_GET_RESULT = (0xA003,"Sandbox: Failed script.result() call.")
ERROR_SCRIPT_EXECUTION = (-0xA003,"Sandbox: Script execution failed.")



class SandboxRun():
    def __init__(self):
        self.terror_code = 0
        self.terror_msg = ""
        self.error_code = 0
        self.error_msg  = ""
        self.call = {'benign':self.benign,
                     'exploit':self.exploit,
                     'setflag':self.setflag,
                     'getflag':self.getflag}

    def exit(self):

        self.error_msg += " . Command: "+str(sys.argv)
        print '\n',
        print json.dumps({'ERROR':self.error_code,'ERROR_MSG':self.error_msg})

        #try:
        #    os.killpg(os.getpid(),9) #make sure all the child processes are killed
        #except:
        #    pass

        exit(0) #this will not be called


    def clean_exit(self):
        if 'ERROR' not in self.result:
            #e.g. team submited code
            self.result['ERROR']=0
        if 'ERROR_MSG' not in self.result:
            self.result['ERROR_MSG']='No message was provided by the script.'

        print '\n',
        print json.dumps(self.result)
        try:
            os.killpg(os.getpid(),9) #make sure all the child processes are killed
        except:
            pass
        exit() #this will not be called

    def benign(self):
        try:
            self.script = imp.load_source('benign',self.script_path)
            self.script = self.script.Benign()
            self.script.execute(self.ip,self.port,self.flag_id,self.cookie)
            #self.script.execute(self.ip,self.port)
        except Exception as e:
            self.terror_code,self.terror_msg = ERROR_SCRIPT_EXECUTION
            self.terror_msg+=" "+str(e)
            self.exit()

    def exploit(self):
        try:
            self.script = imp.load_source('exploit',self.script_path)
            self.script = self.script.Exploit()
            self.script.execute(self.ip,self.port,self.flag_id)
        except Exception as e:
            self.terror_code,self.terror_msg = ERROR_SCRIPT_EXECUTION
            self.terror_msg+=" "+str(e)
            self.exit()

    def setflag(self):
        try:
            self.script = imp.load_source('setflag',self.script_path)
            self.script = self.script.SetFlag()
            self.script.execute(self.ip,self.port,self.flag)
        except Exception as e:
            self.terror_code,self.terror_msg = ERROR_SCRIPT_EXECUTION
            self.terror_msg+=" "+str(e)
            self.exit()
        
    def getflag(self):
        try:
            self.script = imp.load_source('getflag',self.script_path)
            self.script = self.script.GetFlag()
            self.script.execute(self.ip,self.port,self.flag_id,self.cookie)
        except Exception as e:
            self.terror_code,self.terror_msg = ERROR_SCRIPT_EXECUTION
            self.terror_msg+=" "+str(e)
            self.exit()

    def thread_proc(self):
        sys.path.append(os.path.dirname(self.script_path))
        self.call[self.script_type]()



    def update_from_args(self):
        self.timeout = int(sys.argv[2])
        self.script_type = sys.argv[3]
        self.script_path = sys.argv[4]
        self.ip = str(sys.argv[5])
        self.port = int(sys.argv[6])
        if self.script_type == 'exploit':
            self.flag_id = sys.argv[7]
        if self.script_type == 'setflag':
            self.flag = sys.argv[7]
        if self.script_type == 'getflag' or self.script_type == 'benign':
            self.flag_id = sys.argv[7]
            self.cookie = sys.argv[8]

    def run(self):
        try:
            self._run()
        except Exception as e:
            self.error_code,self.error_msg = ERROR_SCRIPT_EXECUTION
            self.error_msg+=" "+str(e)
            self.exit()
    

    def _run(self):
        # args are script_id,timeout,script_type,script_path,ip,port,args..

        if len(sys.argv)<6:
            self.error_code,self.error_msg = ERROR_ARG
            self.error_msg += " : "+str(sys.argv)
            self.exit()
        try:
            self.update_from_args()
        except Exception as e:
            self.error_code,self.error_msg = ERROR_ARG_PARSE
            self.error_msg+=" "+str(e)
            self.exit()

        td = Thread(target = self.thread_proc)
        td.daemon = True
        td.start()
        td.join(self.timeout)
        
        #ignore even if it's timeout and move on.
        #if td.isAlive():
        #    self.error_code,self.error_msg = ERROR_TIMEOUT
        #    self.exit()
            
        if self.terror_code !=0:
            self.error_code = self.terror_code
            self.error_msg = self.terror_msg
            self.exit()

        try:
            self.result = self.script.result()
            self.clean_exit()
        except Exception as e:
            self.error_code,self.error_msg = ERROR_GET_RESULT
            self.error_msg+=" "+str(e)
            self.exit()
        
    

def main():
    s = SandboxRun()
    s.run()

if __name__ == '__main__':
    main()

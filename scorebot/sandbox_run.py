import os,sys,subprocess
import random
import string
session = ''.join(random.choice(string.ascii_lowercase + string.digits) for x in range(16))
#os.environ["LD_PRELOAD"] ="/ictf/repository/attack/common/connect.so"
#os.environ["SCRIPTID"] = sys.argv[1]
#os.environ["FLOWSESSION"]=session
os.chdir('/tmp/')
#print 'Running as: '+subprocess.check_output(['whoami'])
try:
    subprocess.call(['/usr/bin/python',
                 sys.argv[0].replace('sandbox_run.py','main_sandbox_run.py')]+
                sys.argv[1:])
except Exception as e:
    print e
exit(0)

import subprocess
import time
name = 'p'
for i in range(51, 101):
    namec = name + str(i)    
    print 'launching: ', namec, '\n'
    subprocess.Popen(['python', 'rand_shit.py', namec, namec])

# time.sleep(300)
# print "second round\n"

# for i in range(51, 101):
#     namec = name + str(i)    
#     print 'launching: ', namec, '\n'
#     subprocess.Popen(['python', 'rand_shit.py', namec, namec])

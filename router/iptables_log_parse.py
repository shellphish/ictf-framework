import subprocess as sub
from sys import argv
import re


if len(argv) != 2:
	print "Please enter a time as argv[1]"
	exit()

output = open('/var/log/kern.log', 'r').read()#.split('\n')
regex = "(Mar [1-9]+\s[0-9]+:[0-9]+:[0-9]+).*Connection Limit Reached.*SRC=([0-9]*.[0-9]*.[0-9]*.[0-9]*) DST=([0-9]*.[0-9]*.[0-9]*.[0-9]*).*SPT=([0-9]*) DPT=([0-9]*)"
delta = int(argv[1])
time_regex = "Mar [0-9]+ [0-9]+:([0-9]+):"
sus_conns = re.findall(regex, output)
init_time = int(re.match(time_regex, sus_conns[-1][0]).group(1))

target = init_time - delta if init_time - delta > 0 else init_time - delta + 60


for grp in reversed(sus_conns):
	minutes = int(re.match(time_regex, grp[0]).group(1))
	if minutes == target:
		break
	print grp
		

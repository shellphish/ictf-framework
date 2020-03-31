#!/bin/bash
#
# run_tcp_dump		start the tcp_dumpservice.py to pull grab logs
#
# chkconfig: 2345 81 31
# description: Used as a part of ictf processes
# processname: run_tcp_dump
# pidfile: /var/run/sendmail.pid


# source function library
. /etc/rc.d/init.d/functions

RETVAL=0
PY_SCRIPT="ictf-tcpdump.py"
lockfile=/var/lock/subsys/$PY_SCRIPT
tcp_dump="tcpdump"

DAEMON_PATH="/opt/ictf/router"
DAEMONOPTS="$DAEMON_PATH/$PY_SCRIPT"
DAEMON="/usr/bin/python"
DAEMON_CMD="$DAEMON $DAEMONOPTS"
echo $DAEMON_CMD
# Some functions to make the below more readable
PID_FILE=/var/run/run_tcp_dump.pid

#runlevel=$(set -- $(runlevel); eval "echo \$$#" )

start()
{

    if [ -f "$PID_FILE" ]; then
        echo "Start of $PY_SCRIPT failed because the $PID_FILE exists, attempting to stop"
        PID=`cat "$PID_FILE"`
        kill -0 $PID &>/dev/null
        RETVAL=$?
        if [ $RETVAL -eq 0 ] ; then
            stop
        else
            echo "No associated process found, deleting PID file and resuming start process."
            rm -f $PID_FILE
        fi
        if [ -f "$PID_FILE" ]; then
            echo "Second start of $PY_SCRIPT failed because the $PID_FILE STILL exists, exiting..."
            return 99
        fi
    fi

	cd $DAEMON_PATH
    echo -n $"Starting $PY_SCRIPT: "
	#PID=`$DAEMON_CMD > /dev/null 2>&1 & echo $!`
	$DAEMON_CMD &
	PID=$!
	sleep 1
    #TEST_PID=`ps -p $PID -o pid=`
    kill -0 $PID &>/dev/null
    RETVAL=$?
	if [ -z $PID ] || [ $RETVAL -ne 0 ] ; then
        failure
        echo
        #echo "pid = $PID testpid = $TEST_PID "
	else
	    success
	    echo
	    #echo "pid = $PID testpid = $TEST_PID "
        echo $PID > $PID_FILE
        touch $lockfile
	fi

	return $RETVAL
}

stop()
{
	if [ ! -f "$PID_FILE" ]; then
		# not running; per LSB standards this is "ok"
		action $"Stopping $PY_SCRIPT: with NO PID FILE" /bin/true
		pkill -f $PY_SCRIPT
		return 0
	fi
	PID=`cat "$PID_FILE"`
	if [ -n "$PID" ]; then
		/bin/kill "$PID" >/dev/null 2>&1
		RETVAL=$?
		if [ $RETVAL -ne 0 ]; then
			RETVAL=1
			action $"Stopping $PY_SCRIPT: " /bin/false
		else
			action $"Stopping $PY_SCRIPT: " /bin/true
		fi
	else
		# failed to read pidfile
		action $"Stopping $PY_SCRIPT: " /bin/false
		RETVAL=4
	fi
	# if we are in halt or reboot runlevel kill all running sessions
	# so the TCP connections are closed cleanly
	if [ "x$runlevel" = x0 -o "x$runlevel" = x6 ] ; then
	    trap '' TERM
	    pkill -9 -f $PY_SCRIPT
	    trap TERM
	fi
	[ $RETVAL -eq 0 ] && rm -f $lockfile
	rm -f "$PID_FILE"
    return $RETVAL
}

restart() {
	stop
	start
}

case "$1" in
	start)
		start
		;;
	stop)
	    stop
		;;
	restart)
		restart
		;;
	status)
	    printf "%-50s" "Checking $PY_SCRIPT..."
        if [ -f $PID_FILE ]; then
            PID=`cat $PID_FILE`
            printf "checking $PID"
            if [ -z "`ps axf | grep ${PID} | grep -v grep`" ]; then
                printf "%s\n" "Process dead but pidfile exists"
            else
                echo "Running"
            fi
        else
            printf "%s\n" "Service not running"
        fi

		;;
	*)
		echo $"Usage: $0 {start|stop|restart|status}"
		RETVAL=2
esac
exit $RETVAL




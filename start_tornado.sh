#!/bin/bash
LOGFILE=/var/log/tornado.log
PYTHON=/usr/bin/python

# Authenticate our daemon
(
    while true; do
	kinit daemon/zephyrplus.xvm.mit.edu -k -t /ZephyrPlus/zephyrplus-new-keytab
	sleep 3600;
    done
) &

# Start the tornado server
exec $PYTHON /ZephyrPlus/zephyrplus.py 2>> $LOGFILE

#!/bin/bash
LOGFILE=/var/log/tornado.log
PYTHON=/usr/bin/python

# Start the tornado server
$PYTHON /ZephyrPlus/zephyrplus.py 2>> $LOGFILE &
TORNADO_PID="$!"

# Kill children on exit signal
trap "(kill $TORNADO_PID; kill $INSERT_PID)" exit INT TERM

# Wait for child processes to exit
wait


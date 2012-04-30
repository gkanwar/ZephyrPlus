#!/bin/bash
LOGFILE=/var/log/tornado.log
PYTHON=/usr/bin/python

$PYTHON /ZephyrPlus/zephyrplus.py 2>> $LOGFILE &
$PYTHON /ZephyrPlus/insert_zephyr.py >> $LOGFILE 2>> $LOGFILE &

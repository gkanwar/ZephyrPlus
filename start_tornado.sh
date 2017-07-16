#!/bin/bash -e
LOGFILE=/var/log/tornado.log
PYTHON=/usr/bin/python

kinit="kinit daemon/zephyrplus.xvm.mit.edu -k -t /ZephyrPlus/zephyrplus-new-keytab"

tickets_dir=$(mktemp -d)
ticket_file="$tickets_dir/krb5cc"
ticket_file_swap="$tickets_dir/krb5cc.swp"
export KRB5CCNAME="FILE:$ticket_file"
export KRB_TICKET_SWAP=$ticket_file_swap

# Authenticate our daemon
$kinit
(
    while true; do
        KRB5CCNAME="FILE:$ticket_file_swap" $kinit || true
        sleep 3600;
    done
) &

# Start the tornado server
exec $PYTHON /ZephyrPlus/zephyrplus.py 2>> $LOGFILE

#! /bin/bash
LOGFILE=/var/log/zpd.log
kinit daemon/zephyrplus.xvm.mit.edu -k -t /ZephyrPlus/zephyrplus-new-keytab
zwgc -subfile /ZephyrPlus/.zephyrs.subs -f /ZephyrPlus/.zwgc.desc -ttymode -nofork >> "$LOGFILE" &

# Store the child PID
CHILD="$!"

# Kill chid when start-stop-daemon sends us a kill signal
trap "kill $CHILD" exit INT TERM

# Wait for child process to exit
wait

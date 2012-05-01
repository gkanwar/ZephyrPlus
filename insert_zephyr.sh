#! /bin/bash

# add zephyr to incoming zephyrs fifo pipe
# Script Arugments:
# (1) class, (2) instance, (3) recipient, (4) sender, (5) body, (6) signature

set -f

PIPE="incomingZephyrs.pipe"
LOCK="$PIPE.lock"

if [[ ! -p $PIPE ]]
then
	if [[ -e $PIPE ]]
   	then
		echo "Removing file: $PIPE"
		rm $PIPE
	fi
	echo "Creating pipe: $PIPE"
	mkfifo $PIPE
fi

#echo "arguments $#"
#echo "message<$5>"

DELIMITOR=`echo -e "\0037"`

#lock the file or wait (up to forever) until aquisition of lock
#echo "trying to acquire lock"
flock -x $LOCK -c "(
	set -f;
	echo -n \"$1\" > $PIPE;
	echo -n \"$DELIMITOR\" > $PIPE;
	echo -n \"$2\" > $PIPE;
	echo -n \"$DELIMITOR\" > $PIPE;
	echo -n \"$3\" > $PIPE;
	echo -n \"$DELIMITOR\" > $PIPE;
	echo -n \"$4\" > $PIPE;
	echo -n \"$DELIMITOR\" > $PIPE;
	echo -n \"$5\" > $PIPE;
	echo -n \"$DELIMITOR\" > $PIPE;
	echo -n \"$6\" > $PIPE;
	echo -n \"$DELIMITOR\" > $PIPE;
	)"
echo "insert_zephyr.sh:""$*"
#echo "successfully sent message down the pipe"

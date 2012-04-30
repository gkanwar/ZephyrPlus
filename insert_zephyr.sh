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

#lock the file or wait (up to forever) until aquisition of lock
#echo "trying to acquire lock"
flock -x $LOCK -c "(
	set -f;
	echo $1 > $PIPE;
	echo $2 > $PIPE;
	echo $3 > $PIPE;
	echo $4 > $PIPE;
	echo $5 > $PIPE;
	echo $6 > $PIPE;
	echo -e \"\0\" > $PIPE;
	)"
echo "$*"
#echo "successfully sent message down the pipe"

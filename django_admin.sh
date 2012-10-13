#! /bin/bash
PYTHON=/usr/bin/python2
DJANGO_ROOT=.

cd $DJANGO_ROOT
$PYTHON manage.py runserver 0.0.0.0:8000 > /dev/null &
DJANGO_PID="$!"

# Kill children on exit signal
trap "(kill $DJANGO_PID)" exit INT TERM

# Wait for child process to exit
wait

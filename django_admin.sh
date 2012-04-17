#! /bin/bash
PYTHON=/usr/bin/python2
DJANGO_ROOT=.

cd $DJANGO_ROOT
$PYTHON manage.py runserver 0.0.0.0:8000 > /dev/null

#!/usr/bin/env python2
import os, sys
import datetime, time

# PyZephyr Library for subscribing and receiving
import zephyr, _zephyr
# Django Module for interacting with our database
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from models import Zephyr, Subscription
# httplib to signal tornado to update
import httplib

LOGFILE_NAME = "/var/log/zpd.log"
checkSubs=False
retrySubTimeout = 0.01

## First we get a list of subscriptions from the database
## Filter these subscriptions to only those with class fields
## With only want subscriptions with <class,*,*>
## Add these to the subscription set

# loads the subscriptions from the database into the Subscriptions class
# subscribes using Subscriptions.sub
# returns the singleton Subscriptions
def loadSubscriptions():
    subs = zephyr.Subscriptions()
    toplevelClasses = Subscription.objects.filter(instance='*',recipient='*')
    for sub in toplevelClasses:
        try:
            subs.add((str(sub.class_name), str(sub.instance), str(sub.recipient)))
            time.sleep(0.01) # Loading too quickly 
        except IOError as (errno, strerror):
            # SERVNAK: Usually is a temp. issue, loading too quickly. Try to sub once
            # more, but give up after a second try
            if strerror == "SERVNAK received":
                try:
                    time.sleep(retrySubTimeout)
                    subs.add((str(sub.class_name), str(sub.instance), str(sub.recipient)))
                except IOError:
                     continue
            else:
                sys.stderr.write("Could not handle IOError " + str(errno) + " " + strerror)
                sys.stderr.write("Exitting...")
                sys.exit(2)
    return subs


# Inserts a received ZNotice into our database
def insertZephyr(zMsg):
    # Create a valid destination field for our zephyr
    s = Subscription.objects.get_or_create(class_name=zMsg.cls.lower(), instance=zMsg.instance.lower(), recipient=zMsg.recipient.lower())[0]

    # Sender + Signature Processing
    sender = zMsg.sender
    signature = zMsg.fields[0]
    if sender == "daemon/zephyrplus.xvm.mit.edu":
        sender = signature.split(" ")[0]
        if signature.find("(") != -1:
            signature = signature[signature.find("(")+1:signature.rfind(")")]
        else:
            signature = ""
    signature = signature.replace(") (via ZephyrPlus", "").replace("via ZephyrPlus", "")

    # Database insert
    msg = zMsg.fields[1].rstrip()
    z = Zephyr(message=msg, sender=sender, date=datetime.datetime.now(), dst=s, signature=signature)
    z.save()
    log("Zephyr(" + str(z.id) + "): " + str(s) + " " + sender + " " + msg + " " + signature)

    # Tell server to update
    z_id = z.id
    #sys.stdout.write(str(z_id))
    #sys.stdout.flush()
    try:
        h = httplib.HTTPConnection('localhost:8888')
        h.request('GET', '/update?id='+str(z_id))
        r = h.getresponse()
        #print(r.status, r.reason)
    except:
        print("Could not notify tornado server of new zephyr.")

# Checks if our tornado process has sent us any new subs
# If we have a new sub, add it to the subscription list
# Modifies subs
def checkForNewSubs(subs):
    if not checkSubs:
        return
    tornadoInput = sys.stdin.read()
    if tornadoInput == '':
        return
    else:
        while tornadoInput != '':
            (cls,inst,recip) = tornadoInput.split("\0")
            log("Sub: " + cls + "," + inst + "," + recip)
            subs.add((str(cls), str(inst), str(recip)))
            tornadoInput = sys.stdin.readline()

# Writes debuging messages to logfile
def log(msg):
    logfile = open(LOGFILE_NAME, "a")
    datestr = datetime.datetime.now().strftime("[%m/%d %H:%M]")
    logfile.write(datestr + " " + msg + "\n")
    logfile.close()

def main():
    log("loadZephyr.py starting...")
    subs = loadSubscriptions()
    log("Loaded " + str(len(subs)) + " subscriptions.")

    while True:
        zMsg = _zephyr.receive()
        if zMsg != None:
            insertZephyr(zMsg)
        else:
            time.sleep(0.005)
        checkForNewSubs(subs)

if __name__ == "__main__":
    main()

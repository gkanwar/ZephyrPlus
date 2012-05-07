#!/usr/bin/env python2
import os, sys
import datetime, time
import threading
import Queue

# PyZephyr Library for subscribing and receiving
import zephyr, _zephyr
# Django Module for interacting with our database
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from models import Zephyr, Subscription
# httplib to signal tornado to update
import httplib

class ZephyrLoader(threading.Thread):
    LOGFILE_NAME = "/var/log/zpd.log"
    checkSubs=True
    retrySubTimeout = 0.01
    newSubQueue = Queue.Queue()

    def addSubscription(self, sub):
        self.newSubQueue.put(sub)

    ## First we get a list of subscriptions from the database
    ## Filter these subscriptions to only those with class fields
    ## With only want subscriptions with <class,*,*>
    ## Add these to the subscription set

    # loads the subscriptions from the database into the Subscriptions class
    # subscribes using Subscriptions.sub
    # returns the singleton Subscriptions
    def loadSubscriptions(self):
        subs = zephyr.Subscriptions()
        toplevelClasses = Subscription.objects.filter(instance='*',recipient='*')
        for sub in toplevelClasses:
            self.subscribe(sub, subs)
        return subs

    def subscribe(self, sub, subs):
        try:
            subs.add((str(sub.class_name), str(sub.instance), str(sub.recipient)))
            time.sleep(0.01) # Loading too quickly 
        except IOError as (errno, strerror):
            # SERVNAK: Usually is a temp. issue, loading too quickly. Try to sub once
            # more, but give up after a second try
            if strerror == "SERVNAK received":
                try:
                    time.sleep(self.retrySubTimeout)
                    subs.add((str(sub.class_name), str(sub.instance), str(sub.recipient)))
                except IOError:
                    return
            else:
                sys.stderr.write("Could not handle IOError " + str(errno) + " " + strerror)
                sys.stderr.write("Exitting...")
                sys.exit(2)


    # Inserts a received ZNotice into our database
    def insertZephyr(self, zMsg):
        # Check that the msg is an actual message and not other types.
        if zMsg.kind != 2: # ACKED
            if zMsg.kind != 5: #SERVACK
                self.log("Recieved a " + str(zMsg.kind) + " notice")
                self.log("NOTICE: " + zMsg.cls + " " + zMsg.instance + " " + zMsg.recipient + 
                        " " + zMsg.sender + " " + zMsg.fields[1] + " " + zMsg.fields[0])
            return
        # Create a valid destination field for our zephyr
        recipient = zMsg.recipient.lower()
        if recipient == '':
            recipient = '*'
        s = Subscription.objects.get_or_create(class_name=zMsg.cls.lower(), instance=zMsg.instance.lower(), recipient=recipient)[0]

        # Sender + Signature Processing
        athena = '@ATHENA.MIT.EDU'
        if (len(zMsg.sender) >= len(athena)) and (zMsg.sender[-len(athena):] == athena):
            sender = zMsg.sender[:-len(athena)]
        else:
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
        self.log("Zephyr(" + str(z.id) + "): " + str(s) + " " + sender + " " + msg + " " + signature)

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
    def checkForNewSubs(self,subs):
        if not self.checkSubs:
            return
        #tornadoInput = sys.stdin.read()
        #if tornadoInput == '':
        #    return
        #else:
            #(cls,inst,recip) = tornadoInput.split("\0")
        while not self.newSubQueue.empty():
            sub = self.newSubQueue.get()
            self.log("Sub: " + sub.class_name + "," + sub.instance + "," + sub.recipient)
            self.subscribe(sub, subs)
            #tornadoInput = sys.stdin.readline()

    # Writes debuging messages to logfile
    def log(self,msg):
        logfile = open(self.LOGFILE_NAME, "a")
        datestr = datetime.datetime.now().strftime("[%m/%d %H:%M]")
        logfile.write(datestr + " " + msg + "\n")
        logfile.close()

    def run(self):
        self.log("loadZephyr.py starting...")
        subs = self.loadSubscriptions()
        self.log("Loaded " + str(len(subs)) + " subscriptions.")

        while True:
            zMsg = _zephyr.receive()
            if zMsg != None:
                self.insertZephyr(zMsg)
            else:
                time.sleep(0.05)
            self.checkForNewSubs(subs)


# If we call from main, don't spawn a thread, just execute run()
#def main():
#    t = ZephyrLoader()
#    t.run()
#
#if __name__ == "__main__":
#    main()
# vim: set expandtab:

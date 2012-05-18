#!/usr/bin/env python2
import os, sys
import datetime, time
import threading
import Queue
import socket

# PyZephyr Library for subscribing and receiving
import zephyr, _zephyr
# Django Module for interacting with our database
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from models import Zephyr, Subscription
from django import db
# httplib to signal tornado to update
import httplib
# Unicode support
import codecs
#Debugger
#import pdb

class ZephyrLoader(threading.Thread):
    LOGFILE_NAME = "/var/log/zpd.log"
    KRB_TICKET_CACHE = "/tmp/krb5cc_33"
    checkSubs = True
    retrySubTimeout = 0.01
    newSubQueue = Queue.Queue()
    lastTicketTime = 0

    def __init__(self, *args, **kwargs):
	threading.Thread.__init__(self, *args, **kwargs)
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.connect(("mit.edu",80))
	self.ip = s.getsockname()[0]
	s.close()

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
        toplevelClasses = Subscription.objects.filter(instance='*', recipient='*')
        db.reset_queries()
        for sub in toplevelClasses:
            self.subscribe(sub, subs)
        return subs

    def subscribe(self, sub, subs):
        try:
            subs.add((sub.class_name.encode("utf-8"), str(sub.instance), str(sub.recipient)))
            # time.sleep(0.01) # Loading too quickly 
        except IOError as (errno, strerror):
            # SERVNAK: Usually is a temp. issue, loading too quickly. Try to sub once
            # more, but give up after a second try
            if strerror == "SERVNAK received":
                try:
                    time.sleep(self.retrySubTimeout)
                    subs.add((sub.class_name.encode("utf-8"), str(sub.instance), str(sub.recipient)))
                except IOError:
                    return
            else:
                sys.stderr.write("Could not handle IOError " + str(errno) + " " + strerror)
                sys.stderr.write("Exitting...")
                sys.exit(2)


    # Inserts a received ZNotice into our database
    def insertZephyr(self, zMsg):
        # Check that the msg is an actual message and not other types.
        if zMsg.kind > 2: # Only allow UNSAFE, UNACKED, ACKED messages
            return

        # Create a valid destination field for our zephyr
        class_name = unicode(zMsg.cls.lower(), 'utf-8')
        instance = unicode(zMsg.instance.lower(), 'utf-8')
        recipient = unicode(zMsg.recipient.lower(), 'utf-8')
        if recipient == '':
            recipient = '*'
        s = Subscription.objects.get_or_create(class_name=class_name, instance=instance, recipient=recipient)[0]

        # Sender + Signature Processing
        athena = '@ATHENA.MIT.EDU'
        if (len(zMsg.sender) >= len(athena)) and (zMsg.sender[-len(athena):] == athena):
            sender = zMsg.sender[:-len(athena)]
        else:
            sender = zMsg.sender

        signature = zMsg.fields[0]
        #if sender == "daemon/zephyrplus.xvm.mit.edu":
            #sender = signature.split(" ")[0]
            #if signature.find("(") != -1:
                #signature = signature[signature.find("(")+1:signature.rfind(")")]
            #else:
                #signature = ""
        signature = signature.replace(") (via ZephyrPlus", "").replace("via ZephyrPlus", "")

        # Authentication check
        if not zMsg.auth and zMsg.uid.address != self.ip:
	    sender += " (UNAUTH)"
	    if 'via zephyrplus' in zMsg.fields[0].lower():
		zephyr.ZNotice(cls=zMsg.cls,
			       instance=zMsg.instance,
			       recipient=zMsg.recipient,
			       opcode='AUTO',
			       message="ZephyrPlus Server\x00" +
			       "The previous zephyr,\n\n" + zMsg.fields[1].strip() + "\n\nwas FORGED (not sent from ZephyrPlus).\n").send()

        # Convert to unicode
        msg = unicode(zMsg.fields[1].rstrip(), 'utf-8')
        sender = unicode(sender, 'utf-8')
        signature = unicode(signature, 'utf-8')

        # Database insert
        z = Zephyr(message=msg, sender=sender, date=datetime.datetime.now(), dst=s, signature=signature)
        z.save()

        #pdb.set_trace()
        logMsg = u"Zephyr(%d): %s %s %s %s" % (z.id, unicode(s), sender, msg, signature)
        self.log(logMsg)

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

        # Clean up our database queries
        db.reset_queries()

    # Checks if our tornado process has sent us any new subs
    # If we have a new sub, add it to the subscription list
    # Modifies subs
    def checkForNewSubs(self, subs):
        if not self.checkSubs:
            return
        while not self.newSubQueue.empty():
            sub = self.newSubQueue.get()
            logMsg = u"Sub: %s %s %s" % (sub.class_name, sub.instance, sub.recipient)
            self.log(logMsg)
            self.subscribe(sub, subs)
    
    # Send an empty subscription request to reload our tickets
    # so zephyrs won't show up as unauthenticated to us
    # whenever we renew tickets
    def renewAuth(self):
        ticketTime = os.stat(self.KRB_TICKET_CACHE).st_mtime
        if ticketTime != self.lastTicketTime:
            zephyr._z.sub('', '', '')
            self.lastTicketTime = ticketTime
            self.log("Sent subscription request")

    # Writes debuging messages to logfile
    def log(self, msg):
        logfile = codecs.open(self.LOGFILE_NAME, "a", encoding="utf-8")
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
            self.renewAuth()


# If we call from main, don't spawn a thread, just execute run()
#def main():
#    t = ZephyrLoader()
#    t.run()
#
#if __name__ == "__main__":
#    main()
# vim: set expandtab:

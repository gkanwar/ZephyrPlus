#!/usr/bin/env python2
import os, sys
import datetime, time
import logging
import threading
import Queue
import traceback

# PyZephyr Library for subscribing and receiving
import zephyr, _zephyr
from zephyr_utils import send_zephyr, receive_zephyr
# Django Module for interacting with our database
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from chat.models import Zephyr, Subscription
from django import db
# httplib to signal tornado to update
import httplib
# Unicode support
import codecs
#Debugger
#import pdb
import django.conf


logger = logging.getLogger('zephyrplus.loader')


class ZephyrLoader(threading.Thread):
    LOGFILE_NAME = django.conf.settings.ZEPHYR_LOGFILE_NAME
    KRB_TICKET_CACHE = "/tmp/krb5cc_%s"%os.getuid()
    if 'KRB5CCNAME' in os.environ:
        KRB_TICKET_CACHE = os.environ['KRB5CCNAME'][5:]
    checkSubs = True
    retrySubTimeout = 0.01
    newSubQueue = Queue.Queue()
    lastTicketTime = 0
    class_names = set()

    def __init__(self, *args, **kwargs):
	threading.Thread.__init__(self, *args, **kwargs)

    def addSubscription(self, sub):
        self.newSubQueue.put(sub)
        for class_name in [sub.class_name,
                           u"un" + sub.class_name,
                           u"unun" + sub.class_name,
                           sub.class_name + u".d"]:
            related_sub, created = Subscription.objects.get_or_create(
                class_name=class_name, instance="*", recipient="*")
            if class_name not in self.class_names:
                self.newSubQueue.put(related_sub)

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
        done = 0
        total = len(toplevelClasses)
        for sub in toplevelClasses:
            self.subscribe(sub, subs)
            done += 1
            if done%100 == 0:
                logger.info('%s/%s subscriptions loaded', done, total)
        return subs

    def subscribe(self, sub, subs):
        while True:
            try:
                subs.add((sub.class_name.encode("utf-8"), '*', '*'))
                self.class_names.add(sub.class_name)
                time.sleep(0.001) # Loading too quickly 
                return
            except IOError as (errno, strerror):
                # SERVNAK: Usually is a temp. issue, loading too quickly.
                if strerror == "SERVNAK received":
                    time.sleep(self.retrySubTimeout)
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
        class_name = zMsg.cls.lower()
        instance = zMsg.instance.lower()
        recipient = zMsg.recipient.lower()
        if recipient == u'':
            recipient = u'*'
        s = Subscription.objects.get_or_create(class_name=class_name, instance=instance, recipient=recipient)[0]

        # Sender + Signature Processing
        athena = u'@ATHENA.MIT.EDU'
        if (len(zMsg.sender) >= len(athena)) and (zMsg.sender[-len(athena):] == athena):
            sender = zMsg.sender[:-len(athena)]
        else:
            sender = zMsg.sender

        while len(zMsg.fields) < 2:
            zMsg.fields = [u''] + zMsg.fields
        signature = zMsg.fields[0]
        msg = zMsg.fields[1].rstrip()
        if django.conf.settings.SIGNATURE is not None:
            signature = signature.replace(") (%s"%django.conf.settings.SIGNATURE, "").replace(django.conf.settings.SIGNATURE, "")

        # Authentication check
        if not zMsg.auth:
	    sender += " (UNAUTH)"
	    if django.conf.settings.SIGNATURE is not None and django.conf.settings.SIGNATURE.lower() in zMsg.fields[0].lower():
		zephyr.ZNotice(cls=zMsg.cls,
			       instance=zMsg.instance,
			       recipient=zMsg.recipient,
			       opcode='AUTO',
			       message="ZephyrPlus Server\x00" +
			       "The previous zephyr,\n\n" + zMsg.fields[1].strip() + "\n\nwas FORGED (not sent from ZephyrPlus).\n").send()

        # Unique id
        zuid = (u"%s %s %s" % (zMsg.uid.time, zMsg.uid.address, sender))[:200]

        # Database insert
        z, inserted = Zephyr.objects.get_or_create(
            zuid=zuid,
            defaults=dict(
                message=msg,
                sender=sender,
                date=datetime.datetime.now(),
                dst=s,
                signature=signature,
            ),
        )

        logger.info(u'Zephyr(%d): %s %s %s (%s)', z.id, s, sender, msg, signature)

        # Subscribe to sender class
        if zMsg.auth and sender not in self.class_names:
            new_sub, created = Subscription.objects.get_or_create(
                class_name=sender, instance="*", recipient="*")
            self.addSubscription(new_sub)

        # Tell server to update
        z_id = z.id
        try:
            h = httplib.HTTPConnection('localhost:%s' % django.conf.settings.PORT)
            h.request('GET', '/update?id='+str(z_id))
            r = h.getresponse()
            #print(r.status, r.reason)
        except:
            logger.warning(u'Could not notify tornado server of new zephyr.', exc_info=True)

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
            logger.info(u'Sub: %s %s %s', sub.class_name, sub.instance, sub.recipient)
            self.subscribe(sub, subs)
    
    # Send an empty subscription request to reload our tickets
    # so zephyrs won't show up as unauthenticated to us
    # whenever we renew tickets
    def renewAuth(self):
        try:
            ticketTime = os.stat(self.KRB_TICKET_CACHE).st_mtime
            if ticketTime != self.lastTicketTime:
                zephyr._z.sub('', '', '')
                self.lastTicketTime = ticketTime
                logger.info(u'Tickets renewed')
        except:
            logger.error(u'Tickets not found', exc_info=True)

    def run(self):
        logger.info(u'loadZephyr.py starting...')
        subs = self.loadSubscriptions()
        logger.info(u'Loaded %s subscriptions.', len(subs))
        self.stop = False

        while not self.stop:
            try:
                zMsg = receive_zephyr()
                if zMsg != None:
                    self.insertZephyr(zMsg)
                else:
                    time.sleep(0.05)
                self.checkForNewSubs(subs)
                self.renewAuth()
            except:
                logger.error(u'Exception in loader loop', exc_info=True)


# If we call from main, don't spawn a thread, just execute run()
#def main():
#    t = ZephyrLoader()
#    t.run()
#
#if __name__ == "__main__":
#    main()
# vim: set expandtab:

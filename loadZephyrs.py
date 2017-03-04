#!/usr/bin/env python

from __future__ import unicode_literals

import datetime
import logging
import os
import sys
import threading
import time
from tornado import gen
from tornado.ioloop import IOLoop, PeriodicCallback
from tornado.queues import Queue

# PyZephyr Library for subscribing and receiving
import zephyr, _zephyr
from zephyr_utils import send_zephyr, receive_zephyr
# Django Module for interacting with our database
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
import django
django.setup()
from chat.models import Zephyr, Subscription
import django.conf


logger = logging.getLogger('zephyrplus.loader')


KRB_TICKET_CACHE = "/tmp/krb5cc_%s"%os.getuid()
if 'KRB5CCNAME' in os.environ:
    KRB_TICKET_CACHE = os.environ['KRB5CCNAME'][5:]


class Subscriber(object):
    '''Class responsible for subscribing to classes.'''

    def __init__(self):
        # Queue of Subscription objects
        self._new_sub_queue = Queue()
        # Set of classes that we are subscribed to or are in the queue
        self._class_names = set()

    def subscribe(self, class_name):
        for related_class in [class_name,
                              'un' + class_name,
                              'unun' + class_name,
                              class_name + '.d']:
            if related_class not in self._class_names:
                sub, created = Subscription.objects.get_or_create(
                    class_name=related_class, instance='*', recipient='*')
                logger.info('Sub %s', sub)
                self._maybe_add_sub_to_queue(sub)

    ## First we get a list of subscriptions from the database
    ## Filter these subscriptions to only those with class fields
    ## With only want subscriptions with <class,*,*>
    ## Add these to the subscription set
    def _load_subscriptions(self):
        logger.debug('getting new subscriptions...')
        for sub in Subscription.objects.filter(instance='*', recipient='*'):
            self._maybe_add_sub_to_queue(sub)
        logger.debug('got new subscriptions')

    def _maybe_add_sub_to_queue(self, sub):
        if sub.class_name not in self._class_names:
            self._new_sub_queue.put_nowait(sub)
            self._class_names.add(sub.class_name)

    @gen.coroutine
    def _process_subs(self):
        while True:
            first_sub = yield self._new_sub_queue.get()
            subs = [first_sub]
            while self._new_sub_queue.qsize() > 0 and len(subs) < 1000:
                subs.append(self._new_sub_queue.get_nowait())

            tuples = [(sub.class_name.encode('utf-8'), '*', '@' + _zephyr.realm())
                      for sub in subs]

            logger.debug('Subscribing to %s subs...', len(tuples))
            _zephyr.subAll(tuples)
            logger.info('Subscribed to %s subs', len(tuples))

    @gen.coroutine
    def start(self):
        self._load_subscriptions()
        # Periodically check for new subs added by other Z+ instances
        PeriodicCallback(self._load_subscriptions, 60 * 1000).start()

        PeriodicCallback(self._process_subs, 1).start()


class Receiver(object):
    '''Class responsible for receiving zephyrs and inserting them into the
    database.'''

    def __init__(self, subscriber, handler):
        self._subscriber = subscriber
        self._handler = handler
        self.lastTicketTime = 0

    # Inserts a received ZNotice into our database
    def _insert_zephyr(self, zMsg):
        # Check that the msg is an actual message and not other types.
        if zMsg.kind > 2: # Only allow UNSAFE, UNACKED, ACKED messages
            return

        # Create a valid destination field for our zephyr
        class_name = zMsg.cls.lower()
        instance = zMsg.instance.lower()
        recipient = zMsg.recipient.lower()
        if recipient == '':
            recipient = '*'
        s = Subscription.objects.get_or_create(class_name=class_name, instance=instance, recipient=recipient)[0]

        # Sender + Signature Processing
        athena = '@ATHENA.MIT.EDU'
        if (len(zMsg.sender) >= len(athena)) and (zMsg.sender[-len(athena):] == athena):
            sender = zMsg.sender[:-len(athena)]
        else:
            sender = zMsg.sender

        while len(zMsg.fields) < 2:
            zMsg.fields = [''] + zMsg.fields
        signature = zMsg.fields[0]
        msg = zMsg.fields[1].rstrip()
        if django.conf.settings.SIGNATURE is not None:
            signature = signature.replace(") (%s"%django.conf.settings.SIGNATURE, "").replace(django.conf.settings.SIGNATURE, "")

        # Authentication check
        if not zMsg.auth:
            sender += ' (UNAUTH)'
            if django.conf.settings.SIGNATURE is not None and django.conf.settings.SIGNATURE.lower() in zMsg.fields[0].lower():
                logger.warning('Received forged zephyr: %r', zMsg.__dict__)
                zephyr.ZNotice(
                    cls=zMsg.cls.encode('utf-8'),
                    instance=zMsg.instance.encode('utf-8'),
                    recipient=zMsg.recipient.encode('utf-8'),
                    opcode='AUTO',
                    fields=[
                        'ZephyrPlus Server',
                        'The previous zephyr,\n\n%r\n\nwas FORGED (not sent from ZephyrPlus).\n' % msg
                    ]
                ).send()

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

        logger.info('Zephyr(%d): %s %s %s (%s)', z.id, s, sender, msg, signature)

        # Subscribe to sender class
        if zMsg.auth:
            self._subscriber.subscribe(sender)

        # Tell server to update
        self._handler(z)

    # Send an empty subscription request to reload our tickets
    # so zephyrs won't show up as unauthenticated to us
    # whenever we renew tickets
    def _renew_auth(self):
        try:
            ticketTime = os.stat(KRB_TICKET_CACHE).st_mtime
            if ticketTime != self.lastTicketTime:
                zephyr._z.sub('', '', '')
                self.lastTicketTime = ticketTime
                logger.info('Tickets renewed')
        except Exception:
            logger.error('Tickets not found', exc_info=True)

    @gen.coroutine
    def _run(self):
        while True:
            try:
                zMsg = receive_zephyr()
                if zMsg != None:
                    self._insert_zephyr(zMsg)
                else:
                    yield gen.sleep(0.05)
                self._renew_auth()
            except Exception:
                logger.error('Exception in loader loop', exc_info=True)

    @gen.coroutine
    def start(self):
        PeriodicCallback(self._run, 1).start()


class ZephyrLoader(object):
    def __init__(self, handler):
        self._subscriber = Subscriber()
        self._receiver = Receiver(self._subscriber, handler)

    def subscribe(self, class_name):
        self._subscriber.subscribe(class_name)

    @gen.coroutine
    def start(self):
        logger.info('loadZephyr.py starting...')
        yield self._subscriber.start()
        yield self._receiver.start()


def main():
    zephyr.init()
    def callback(zMsg):
        print '%s' % zMsg.__dict__
    loader = ZephyrLoader(callback)
    loader.start()
    IOLoop.current().start()


if __name__ == '__main__':
    main()

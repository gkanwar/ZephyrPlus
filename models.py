from django.db import models
from django.db.models import Q
import datetime

APPLICATION_NAME = "chat"

class Zephyr(models.Model):
	message = models.TextField()
	sender = models.CharField(max_length=200)
	date = models.DateTimeField(db_index=True)
	dst = models.ForeignKey('Subscription')
	signature = models.TextField(blank=True, null=True)
	receivers = models.ManyToManyField("Account", blank=True)
	
	def _compute_receivers(self):
	    self.receivers = Account.objects.filter(Q(subscriptions=self.dst)|Q(subscriptions__in=self.dst.parents.all()))

	class Meta:
		app_label = APPLICATION_NAME
		db_table = 'chat_zephyr'

	def __unicode__(self):
		return self.sender + " to " + unicode(self.dst) + " on " + unicode(self.date)

def _on_zephyr_create(sender, instance, created, **kwargs):
    if created and sender == Zephyr:
        instance._compute_receivers()
        instance.save()
models.signals.post_save.connect(_on_zephyr_create, sender=Zephyr)

class Subscription(models.Model):
    class_name = models.CharField(max_length=200)
    instance = models.CharField(max_length=200)
    recipient = models.CharField(max_length=200)
    parents = models.ManyToManyField("self", symmetrical=False, related_name="children")

    def get_filter(self):
        return models.Q(dst=self) | models.Q(dst__parents=self)

    _cached_parents = None
    def get_parents(self):
        if self._cached_parents is None:
	    self._cached_parents = self.parents.all()
	return self._cached_parents
    
    def match(self, zephyr):
        return zephyr.dst == self or self in zephyr.dst.get_parents()

    def _compute_parents(self):
        parents = []
        if self.class_name[:2] == 'un' and len(self.class_name) > 2:
            parents.append(Subscription.objects.get_or_create(class_name=self.class_name[2:], \
                                                              instance=self.instance, \
                                                              recipient=self.recipient)[0])
        if self.class_name[-2:] == '.d' and len(self.class_name) > 2:
            parents.append(Subscription.objects.get_or_create(class_name=self.class_name[:-2], \
                                                              instance=self.instance, \
                                                              recipient=self.recipient)[0])
        if self.instance != '*':
            if self.instance[-2:] == '.d' and len(self.instance) > 2:
                parents.append(Subscription.objects.get_or_create(class_name=self.class_name, \
                                                                  instance=self.instance[:-2], \
                                                                  recipient=self.recipient)[0])
            parents.append(Subscription.objects.get_or_create(class_name=self.class_name, \
                                                              instance='*', \
                                                              recipient=self.recipient)[0])
        self.parents = parents
        for parent in parents:
            self.parents.add(*parent.parents.all())

    class Meta:
        app_label = APPLICATION_NAME
        db_table = 'chat_subscription'

    def __unicode__(self):
        return self.class_name + ", " + self.instance + ", " + self.recipient

def _on_subscription_create(sender, instance, created, **kwargs):
    if created and sender == Subscription:
        instance._compute_parents()
        instance.save()
models.signals.post_save.connect(_on_subscription_create, sender=Subscription)

class Account(models.Model):
	username = models.CharField(max_length=200, primary_key=True)
	subscriptions = models.ManyToManyField(Subscription,blank=True)
	js_data = models.TextField(default='{}')
	
	def get_filter(self):
            #return models.Q(dst__account__username=self.username) | models.Q(dst__parents__account__username=self.username)
            #subs = Subscription.objects.filter(models.Q(account__username=self.username) | models.Q(parents__account__username=self.username))
            #subs = list(subs)
            #return models.Q(dst__in=subs)
            return models.Q(receivers__username=self.username)

	_cached_subscriptions = None
	def get_subscriptions(self):
	    if self._cached_subscriptions is None:
	        self._cached_subscriptions = self.subscriptions.all()
	    return self._cached_subscriptions
	
	def match(self, zephyr):
            for sub in self.get_subscriptions():
                if sub.match(zephyr):
                    return True
            return False
	
	class Meta:
		app_label = APPLICATION_NAME
		db_table = 'chat_account'

	def __unicode__(self):
		return self.username

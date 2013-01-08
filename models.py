from django.db import models
import datetime

APPLICATION_NAME = "chat"

class Zephyr(models.Model):
	message = models.TextField()
	sender = models.CharField(max_length=200)
	date = models.DateTimeField()
	dst = models.ForeignKey('Subscription')
	signature = models.TextField(blank=True, null=True)

	class Meta:
		app_label = APPLICATION_NAME
		db_table = 'chat_zephyr'

	def __unicode__(self):
		return self.sender + " to " + unicode(self.dst) + " on " + unicode(self.date)

class Subscription(models.Model):
    class_name = models.CharField(max_length=200)
    instance = models.CharField(max_length=200)
    recipient = models.CharField(max_length=200)
    parents = models.ManyToManyField("self", symmetrical=False, related_name="children")

    def get_filter(self):
        return models.Q(dst=self) | models.Q(dst__parents=self)

    def match(self, zephyr):
        return zephyr.dst == self or self in zephyr.dst.parents.all()

    def _compute_parents(self):
        parents = []
        if self.class_name[:2] == 'un' and len(self.class_name) > 2:
            parents.append(Subscription.objects.get_or_create(class_name=self.class_name[2:], \
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
            return models.Q(dst__account__username=self.username) | models.Q(dst__parents__account__username=self.username)
	
	def match(self, zephyr):
            for sub in self.subscriptions.all():
                if sub.match(zephyr):
                    return True
            return False
	
	class Meta:
		app_label = APPLICATION_NAME
		db_table = 'chat_account'

	def __unicode__(self):
		return self.username

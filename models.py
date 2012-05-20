from django.db import models
import datetime

APPLICATION_NAME = "zephyrplus"

class Zephyr(models.Model):
	message = models.TextField()
	sender = models.CharField(max_length=20)
	date = models.DateTimeField()
	dst = models.ForeignKey('Subscription')
	signature = models.TextField(blank=True, null=True)

	class Meta:
		app_label = APPLICATION_NAME
		db_table = 'chat_zephyr'

	def __unicode__(self):
		return self.sender + " to " + unicode(self.dst) + " on " + unicode(self.date)

class Subscription(models.Model):
	class_name = models.CharField(max_length=20)
	instance = models.CharField(max_length=20)
	recipient = models.CharField(max_length=20)

	def get_filter(self):
            q = models.Q(dst__class_name=self.class_name)
            q |= models.Q(dst__class_name='un'+self.class_name)
            if self.instance != '*':
                q &= models.Q(dst__instance=self.instance)
            if self.recipient != '*':
                q &= models.Q(dst__recipient=self.recipient)
            return q

	def match(self,zephyr):
		if self.class_name != zephyr.dst.class_name:
			return False
		if self.instance != '*' and self.instance != zephyr.dst.instance:
			return False
		if self.recipient != '*' and self.recipient != zephyr.dst.recipient:
			return False
		return True

	class Meta:
		app_label = APPLICATION_NAME
		db_table = 'chat_subscription'

	def __unicode__(self):
			return self.class_name + ", " + self.instance + ", " + self.recipient

class Account(models.Model):
	username = models.CharField(max_length=20,primary_key=True)
	subscriptions = models.ManyToManyField(Subscription)
	js_data = models.TextField(default='{}')
	
	def get_filter(self):
            q = models.Q()
            for sub in self.subscriptions.all():
                q |= sub.get_filter()
            return q
	
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

from django.db import models
import datetime

class Zephyr(models.Model):
	message = models.TextField()
	sender = models.CharField(max_length=20)
	date = models.DateTimeField()
	dst = models.ForeignKey('Subscription')

	def __unicode__(self):
		return self.sender + " to " + unicode(self.dst) + " on " + unicode(self.date)

class Subscription(models.Model):
	class_name = models.CharField(max_length=20)
	instance = models.CharField(max_length=20)
	recipient = models.CharField(max_length=20)

	def get_filter(self):
		zephyrs = Zephyr.objects.filter(dst__class_name=self.class_name)
		if self.instance != '*':
			zephyrs = zephyrs.filter(dst__instance=self.instance)
		if self.recipient != '*':
			zephyrs = zephyrs.filter(dst__recipient=self.recipient)
		return zephyrs

	def __unicode__(self):
		return self.class_name + ", " + self.instance + ", " + self.recipient

class Account(models.Model):
	username = models.CharField(max_length=20,primary_key=True)
	subscriptions = models.ManyToManyField(Subscription,blank=True)

	def __unicode__(self):
		return self.username


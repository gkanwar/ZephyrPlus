# Create your views here.
from django.http import HttpResponse
from chat.models import Zephyr, Subscription, Account
import datetime
import time

def index(request):
	sub = Subscription(class_name=request.GET['class'], instance=request.GET['instance'], recipient=request.GET['recipient'])
	zephyrs = sub.get_filter()
	if 'date' in request.GET:
		done = False
		while not done:
			zephyrs = sub.get_filter().filter(date__gt=datetime.datetime.fromtimestamp(int(request.GET['date'])))
			done = len(zephyrs) > 0
			time.sleep(1)
			

	return HttpResponse(list(zephyrs.values()))

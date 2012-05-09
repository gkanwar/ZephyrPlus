from chat.models import Zephyr, Account, Subscription
from django.contrib import admin

class SubscriptionAdmin(admin.ModelAdmin):
	list_display = ('class_name', 'instance', 'recipient')
	search_fields  = ['class_name']

class AccountAdmin(admin.ModelAdmin):
	filter_horizontal = ['subscriptions']

admin.site.register(Zephyr)
admin.site.register(Account, AccountAdmin)
admin.site.register(Subscription, SubscriptionAdmin)

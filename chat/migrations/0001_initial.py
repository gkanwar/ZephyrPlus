# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Account',
            fields=[
                ('username', models.CharField(max_length=200, serialize=False, primary_key=True)),
                ('js_data', models.TextField(default=b'{}')),
            ],
            options={
                'db_table': 'chat_account',
            },
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('class_name', models.CharField(max_length=200)),
                ('instance', models.CharField(max_length=200)),
                ('recipient', models.CharField(max_length=200)),
                ('parents', models.ManyToManyField(related_name='children', to='chat.Subscription')),
            ],
            options={
                'db_table': 'chat_subscription',
            },
        ),
        migrations.CreateModel(
            name='Zephyr',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('message', models.TextField()),
                ('sender', models.CharField(max_length=200)),
                ('date', models.DateTimeField(db_index=True)),
                ('signature', models.TextField(null=True, blank=True)),
                ('dst', models.ForeignKey(to='chat.Subscription')),
                ('receivers', models.ManyToManyField(to='chat.Account', blank=True)),
            ],
            options={
                'db_table': 'chat_zephyr',
            },
        ),
        migrations.AddField(
            model_name='account',
            name='subscriptions',
            field=models.ManyToManyField(to='chat.Subscription', blank=True),
        ),
    ]

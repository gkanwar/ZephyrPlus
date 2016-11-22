# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0005_subscription_unique'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscription',
            name='class_name',
            field=models.CharField(max_length=200, db_index=True),
        ),
    ]

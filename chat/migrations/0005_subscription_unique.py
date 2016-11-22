# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0004_zephyr_zuid_unique'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='subscription',
            unique_together=set([('class_name', 'instance', 'recipient')]),
        ),
        migrations.AlterIndexTogether(
            name='subscription',
            index_together=set([('class_name', 'instance', 'recipient')]),
        ),
    ]

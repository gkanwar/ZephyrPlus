# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0003_zephyr_zuid_populate'),
    ]

    operations = [
        migrations.AlterField(
            model_name='zephyr',
            name='zuid',
            field=models.CharField(unique=True, max_length=200),
        ),
    ]

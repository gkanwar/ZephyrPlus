# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0002_zephyr_zuid'),
    ]

    operations = [
        migrations.RunSQL(
            "update chat_zephyr set zuid = id || ' 0.0.0.0 ' || sender where zuid = '';",
            "update chat_zephyr set zuid = '' where zuid like '% 0.0.0.0 %';",
        )
    ]

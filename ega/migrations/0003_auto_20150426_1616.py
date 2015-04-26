# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ega', '0002_auto_20150419_1646'),
    ]

    operations = [
        migrations.AddField(
            model_name='teamstats',
            name='gc',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='teamstats',
            name='gf',
            field=models.PositiveIntegerField(default=0),
        ),
    ]

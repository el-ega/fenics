# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ega', '0003_auto_20150426_1616'),
    ]

    operations = [
        migrations.AddField(
            model_name='tournament',
            name='finished',
            field=models.BooleanField(default=False),
        ),
    ]

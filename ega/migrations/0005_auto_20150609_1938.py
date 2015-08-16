# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('ega', '0004_tournament_finished'),
    ]

    operations = [
        migrations.AddField(
            model_name='egauser',
            name='referred_by',
            field=models.ForeignKey(related_name='referrals', to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='egauser',
            name='referred_on',
            field=models.DateTimeField(null=True),
        ),
    ]

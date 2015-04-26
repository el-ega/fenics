# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import allauth.socialaccount.fields


class Migration(migrations.Migration):

    dependencies = [
        ('socialaccount', '0002_auto_20150418_1939'),
    ]

    operations = [
        migrations.AlterField(
            model_name='socialaccount',
            name='extra_data',
            field=allauth.socialaccount.fields.JSONField(default='{}', verbose_name='extra data'),
        ),
        migrations.AlterField(
            model_name='socialaccount',
            name='provider',
            field=models.CharField(max_length=30, verbose_name='provider', choices=[('facebook', 'Facebook'), ('google', 'Google'), ('twitter', 'Twitter')]),
        ),
        migrations.AlterField(
            model_name='socialapp',
            name='provider',
            field=models.CharField(max_length=30, verbose_name='provider', choices=[('facebook', 'Facebook'), ('google', 'Google'), ('twitter', 'Twitter')]),
        ),
    ]

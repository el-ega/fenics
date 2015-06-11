# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('socialaccount', '0003_auto_20150419_1726'),
    ]

    operations = [
        migrations.AlterField(
            model_name='socialaccount',
            name='provider',
            field=models.CharField(max_length=30, choices=[('facebook', 'Facebook'), ('twitter', 'Twitter'), ('google', 'Google')], verbose_name='provider'),
        ),
        migrations.AlterField(
            model_name='socialapp',
            name='provider',
            field=models.CharField(max_length=30, choices=[('facebook', 'Facebook'), ('twitter', 'Twitter'), ('google', 'Google')], verbose_name='provider'),
        ),
        migrations.AlterField(
            model_name='socialtoken',
            name='token',
            field=models.TextField(help_text='"oauth_token" (OAuth1) or access token (OAuth2)', verbose_name='token'),
        ),
    ]

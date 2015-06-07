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
            field=models.CharField(choices=[('google', 'Google'), ('facebook', 'Facebook'), ('twitter', 'Twitter')], verbose_name='provider', max_length=30),
        ),
        migrations.AlterField(
            model_name='socialapp',
            name='provider',
            field=models.CharField(choices=[('google', 'Google'), ('facebook', 'Facebook'), ('twitter', 'Twitter')], verbose_name='provider', max_length=30),
        ),
        migrations.AlterField(
            model_name='socialtoken',
            name='token',
            field=models.TextField(verbose_name='token', help_text='"oauth_token" (OAuth1) or access token (OAuth2)'),
        ),
    ]

# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-05-18 23:20
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ega', '0006_auto_20151230_1602'),
    ]

    operations = [
        migrations.AddField(
            model_name='match',
            name='knockout',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='teamstats',
            name='zone',
            field=models.CharField(blank=True, default='', max_length=64),
        ),
        migrations.AlterUniqueTogether(
            name='teamstats',
            unique_together=set([('tournament', 'team')]),
        ),
    ]
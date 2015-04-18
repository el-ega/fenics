# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='News',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=256)),
                ('source', models.CharField(max_length=64, blank=True)),
                ('published', models.DateTimeField()),
                ('summary', models.TextField()),
                ('link', models.URLField()),
            ],
            options={
                'ordering': ['-published'],
                'verbose_name': 'News',
                'verbose_name_plural': 'News',
            },
        ),
    ]

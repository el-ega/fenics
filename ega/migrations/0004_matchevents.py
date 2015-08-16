# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ega', '0003_auto_20150426_1616'),
    ]

    operations = [
        migrations.CreateModel(
            name='MatchEvents',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID', auto_created=True)),
                ('video_id', models.CharField(max_length=255, blank=True)),
                ('player', models.CharField(max_length=255)),
                ('minute', models.PositiveIntegerField()),
                ('kind', models.CharField(max_length=64, choices=[('goal', 'Gol'), ('goal-penalty', 'Gol (penal)'), ('yellow-card', 'Tarjeta amarilla'), ('second-yellow-card', 'Doble amarilla'), ('red-card', 'Tarjeta roja'), ('substitution-in', 'Cambio - entra'), ('substitution-out', 'Cambio - sale'), ('unknown', '-')])),
                ('description', models.TextField(blank=True)),
                ('raw_data', models.TextField(blank=True)),
                ('match', models.ForeignKey(to='ega.Match')),
                ('team', models.ForeignKey(to='ega.Team')),
            ],
            options={
                'ordering': ['minute', 'kind'],
            },
        ),
    ]

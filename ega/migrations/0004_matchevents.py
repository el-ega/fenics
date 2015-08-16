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
                ('id', models.AutoField(primary_key=True, verbose_name='ID', serialize=False, auto_created=True)),
                ('player', models.CharField(max_length=255)),
                ('minute', models.PositiveIntegerField()),
                ('kind', models.CharField(choices=[('goal', 'Gol'), ('yellow_card', 'Tarjeta amarilla'), ('red_card', 'Tarjeta roja'), ('substitution_in', 'Cambio - entra'), ('substitution_out', 'Cambio - sale'), ('other', 'Otro')], max_length=64)),
                ('description', models.TextField(blank=True)),
                ('raw_data', models.TextField(blank=True)),
                ('match', models.ForeignKey(to='ega.Match')),
                ('team', models.ForeignKey(to='ega.Team')),
            ],
        ),
    ]

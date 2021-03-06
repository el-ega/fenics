# Generated by Django 2.0.2 on 2018-04-12 01:21

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ega', '0003_auto_20180308_1541'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChampionPrediction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.PositiveIntegerField(default=0)),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('log', models.TextField(blank=True)),
                ('team', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='ega.Team')),
                ('tournament', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ega.Tournament')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='prediction',
            name='last_updated',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='championprediction',
            unique_together={('user', 'tournament')},
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import ega.models
import django.utils.timezone
from django.conf import settings
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='EgaUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(default=django.utils.timezone.now, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(help_text='Required. 30 characters or fewer. Letters, digits and @/./+/-/_ only.', unique=True, max_length=30, verbose_name='username', validators=[django.core.validators.RegexValidator('^[\\w.@+-]+$', 'Enter a valid username.', 'invalid')])),
                ('first_name', models.CharField(max_length=30, verbose_name='first name', blank=True)),
                ('last_name', models.CharField(max_length=30, verbose_name='last name', blank=True)),
                ('email', models.EmailField(max_length=75, verbose_name='email address', blank=True)),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('avatar', models.ImageField(help_text='Se recomienda subir una imagen de (al menos) 100x100', null=True, upload_to='avatars', blank=True)),
                ('invite_key', models.CharField(default=ega.models.rand_str, unique=True, max_length=20)),
                ('groups', models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Group', blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of his/her group.', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(related_query_name='user', related_name='user_set', to='auth.Permission', blank=True, help_text='Specific permissions for this user.', verbose_name='user permissions')),
            ],
            options={
                'abstract': False,
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='League',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('slug', models.SlugField(max_length=200)),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='LeagueMember',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_owner', models.BooleanField(default=False)),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now)),
                ('league', models.ForeignKey(to='ega.League')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Match',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('home_goals', models.IntegerField(null=True, blank=True)),
                ('away_goals', models.IntegerField(null=True, blank=True)),
                ('round', models.CharField(max_length=128, blank=True)),
                ('description', models.CharField(max_length=128, blank=True)),
                ('when', models.DateTimeField(null=True, blank=True)),
                ('location', models.CharField(max_length=200, blank=True)),
                ('referee', models.CharField(max_length=200, blank=True)),
                ('starred', models.BooleanField(default=False)),
                ('suspended', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ('when',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Prediction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('home_goals', models.PositiveIntegerField(null=True, blank=True)),
                ('away_goals', models.PositiveIntegerField(null=True, blank=True)),
                ('trend', models.CharField(max_length=1, editable=False)),
                ('starred', models.BooleanField(default=False)),
                ('score', models.PositiveIntegerField(default=0)),
                ('match', models.ForeignKey(to='ega.Match')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('match__when',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('code', models.CharField(max_length=8, blank=True)),
                ('slug', models.SlugField(unique=True, max_length=200)),
                ('image', models.ImageField(null=True, upload_to='teams', blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='TeamStats',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('won', models.PositiveIntegerField(default=0)),
                ('tie', models.PositiveIntegerField(default=0)),
                ('lost', models.PositiveIntegerField(default=0)),
                ('points', models.PositiveIntegerField(default=0)),
                ('team', models.ForeignKey(to='ega.Team')),
            ],
            options={
                'ordering': ('-points',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Tournament',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('slug', models.SlugField(unique=True, max_length=200)),
                ('published', models.BooleanField(default=False)),
                ('teams', models.ManyToManyField(to='ega.Team')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='teamstats',
            name='tournament',
            field=models.ForeignKey(to='ega.Tournament'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='prediction',
            unique_together=set([('user', 'match')]),
        ),
        migrations.AddField(
            model_name='match',
            name='away',
            field=models.ForeignKey(related_name='away_games', to='ega.Team'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='match',
            name='home',
            field=models.ForeignKey(related_name='home_games', to='ega.Team'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='match',
            name='tournament',
            field=models.ForeignKey(to='ega.Tournament'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='leaguemember',
            unique_together=set([('user', 'league')]),
        ),
        migrations.AddField(
            model_name='league',
            name='members',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, through='ega.LeagueMember'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='league',
            name='tournament',
            field=models.ForeignKey(to='ega.Tournament'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='league',
            unique_together=set([('name', 'tournament'), ('slug', 'tournament')]),
        ),
    ]

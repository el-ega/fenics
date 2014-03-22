# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Tournament'
        db.create_table(u'ega_tournament', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=200)),
            ('published', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'ega', ['Tournament'])

        # Adding M2M table for field teams on 'Tournament'
        m2m_table_name = db.shorten_name(u'ega_tournament_teams')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('tournament', models.ForeignKey(orm[u'ega.tournament'], null=False)),
            ('team', models.ForeignKey(orm[u'ega.team'], null=False))
        ))
        db.create_unique(m2m_table_name, ['tournament_id', 'team_id'])

        # Adding model 'Team'
        db.create_table(u'ega_team', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=200)),
            ('image', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True)),
        ))
        db.send_create_signal(u'ega', ['Team'])

        # Adding model 'Match'
        db.create_table(u'ega_match', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('home', self.gf('django.db.models.fields.related.ForeignKey')(related_name='home_games', to=orm['ega.Team'])),
            ('away', self.gf('django.db.models.fields.related.ForeignKey')(related_name='away_games', to=orm['ega.Team'])),
            ('home_goals', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('away_goals', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('tournament', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ega.Tournament'])),
            ('when', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('location', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('referee', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
        ))
        db.send_create_signal(u'ega', ['Match'])

        # Adding model 'Prediction'
        db.create_table(u'ega_prediction', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('match', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ega.Match'])),
            ('home_goals', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('away_goals', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('starred', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('score', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'ega', ['Prediction'])

        # Adding unique constraint on 'Prediction', fields ['user', 'match']
        db.create_unique(u'ega_prediction', ['user_id', 'match_id'])

        # Adding model 'League'
        db.create_table(u'ega_league', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=200)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=200)),
            ('tournament', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['ega.Tournament'])),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
        ))
        db.send_create_signal(u'ega', ['League'])


    def backwards(self, orm):
        # Removing unique constraint on 'Prediction', fields ['user', 'match']
        db.delete_unique(u'ega_prediction', ['user_id', 'match_id'])

        # Deleting model 'Tournament'
        db.delete_table(u'ega_tournament')

        # Removing M2M table for field teams on 'Tournament'
        db.delete_table(db.shorten_name(u'ega_tournament_teams'))

        # Deleting model 'Team'
        db.delete_table(u'ega_team')

        # Deleting model 'Match'
        db.delete_table(u'ega_match')

        # Deleting model 'Prediction'
        db.delete_table(u'ega_prediction')

        # Deleting model 'League'
        db.delete_table(u'ega_league')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'ega.league': {
            'Meta': {'object_name': 'League'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '200'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200'}),
            'tournament': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['ega.Tournament']"})
        },
        u'ega.match': {
            'Meta': {'object_name': 'Match'},
            'away': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'away_games'", 'to': u"orm['ega.Team']"}),
            'away_goals': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'home': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'home_games'", 'to': u"orm['ega.Team']"}),
            'home_goals': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'referee': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'tournament': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['ega.Tournament']"}),
            'when': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        u'ega.prediction': {
            'Meta': {'unique_together': "(('user', 'match'),)", 'object_name': 'Prediction'},
            'away_goals': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'home_goals': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'match': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['ega.Match']"}),
            'score': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'starred': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'ega.team': {
            'Meta': {'object_name': 'Team'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200'})
        },
        u'ega.tournament': {
            'Meta': {'object_name': 'Tournament'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'published': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200'}),
            'teams': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['ega.Team']", 'symmetrical': 'False'})
        }
    }

    complete_apps = ['ega']
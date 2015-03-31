# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Match.round'
        db.add_column(u'ega_match', 'round',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=128, blank=True),
                      keep_default=False)

    def backwards(self, orm):
        # Deleting field 'Match.round'
        db.delete_column(u'ega_match', 'round')


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
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'ega.egauser': {
            'Meta': {'object_name': 'EgaUser'},
            'avatar': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invite_key': ('django.db.models.fields.CharField', [], {'default': "u'QFMnY3FfX5hgiFUFT5rY'", 'unique': 'True', 'max_length': '20'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'ega.league': {
            'Meta': {'ordering': "[u'name']", 'unique_together': "((u'name', u'tournament'), (u'slug', u'tournament'))", 'object_name': 'League'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['ega.EgaUser']", 'through': u"orm['ega.LeagueMember']", 'symmetrical': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '200'}),
            'tournament': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['ega.Tournament']"})
        },
        u'ega.leaguemember': {
            'Meta': {'unique_together': "((u'user', u'league'),)", 'object_name': 'LeagueMember'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_owner': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'league': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['ega.League']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['ega.EgaUser']"})
        },
        u'ega.match': {
            'Meta': {'ordering': "(u'when',)", 'object_name': 'Match'},
            'away': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'away_games'", 'to': u"orm['ega.Team']"}),
            'away_goals': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'home': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'home_games'", 'to': u"orm['ega.Team']"}),
            'home_goals': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'referee': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'round': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'starred': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'tournament': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['ega.Tournament']"}),
            'when': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        u'ega.prediction': {
            'Meta': {'ordering': "(u'match__when',)", 'unique_together': "((u'user', u'match'),)", 'object_name': 'Prediction'},
            'away_goals': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'home_goals': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'match': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['ega.Match']"}),
            'score': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'starred': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'trend': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['ega.EgaUser']"})
        },
        u'ega.team': {
            'Meta': {'object_name': 'Team'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '8', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '200'})
        },
        u'ega.teamstats': {
            'Meta': {'ordering': "(u'-points',)", 'object_name': 'TeamStats'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lost': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'points': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'team': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['ega.Team']"}),
            'tie': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'tournament': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['ega.Tournament']"}),
            'won': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'})
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
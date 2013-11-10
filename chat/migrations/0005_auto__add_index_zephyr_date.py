# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding index on 'Zephyr', fields ['date']
        db.create_index('chat_zephyr', ['date'])


    def backwards(self, orm):
        # Removing index on 'Zephyr', fields ['date']
        db.delete_index('chat_zephyr', ['date'])


    models = {
        'chat.account': {
            'Meta': {'object_name': 'Account'},
            'js_data': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'subscriptions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['chat.Subscription']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '200', 'primary_key': 'True'})
        },
        'chat.subscription': {
            'Meta': {'object_name': 'Subscription'},
            'class_name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'instance': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'parents': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'children'", 'symmetrical': 'False', 'to': "orm['chat.Subscription']"}),
            'recipient': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'chat.zephyr': {
            'Meta': {'object_name': 'Zephyr'},
            'date': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'dst': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['chat.Subscription']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'receivers': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['chat.Account']", 'symmetrical': 'False', 'blank': 'True'}),
            'sender': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'signature': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['chat']
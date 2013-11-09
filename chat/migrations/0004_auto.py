# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding M2M table for field receivers on 'Zephyr'
        db.create_table('chat_zephyr_receivers', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('zephyr', models.ForeignKey(orm['chat.zephyr'], null=False)),
            ('account', models.ForeignKey(orm['chat.account'], null=False))
        ))
        db.create_unique('chat_zephyr_receivers', ['zephyr_id', 'account_id'])


    def backwards(self, orm):
        # Removing M2M table for field receivers on 'Zephyr'
        db.delete_table('chat_zephyr_receivers')


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
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'dst': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['chat.Subscription']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'receivers': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['chat.Account']", 'symmetrical': 'False', 'blank': 'True'}),
            'sender': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'signature': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['chat']
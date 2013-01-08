# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Zephyr'
        db.create_table('chat_zephyr', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('message', self.gf('django.db.models.fields.TextField')()),
            ('sender', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('date', self.gf('django.db.models.fields.DateTimeField')()),
            ('dst', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['chat.Subscription'])),
            ('signature', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('chat', ['Zephyr'])

        # Adding model 'Subscription'
        db.create_table('chat_subscription', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('class_name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('instance', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('recipient', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal('chat', ['Subscription'])

        # Adding model 'Account'
        db.create_table('chat_account', (
            ('username', self.gf('django.db.models.fields.CharField')(max_length=200, primary_key=True)),
            ('js_data', self.gf('django.db.models.fields.TextField')(default='{}')),
        ))
        db.send_create_signal('chat', ['Account'])

        # Adding M2M table for field subscriptions on 'Account'
        db.create_table('chat_account_subscriptions', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('account', models.ForeignKey(orm['chat.account'], null=False)),
            ('subscription', models.ForeignKey(orm['chat.subscription'], null=False))
        ))
        db.create_unique('chat_account_subscriptions', ['account_id', 'subscription_id'])


    def backwards(self, orm):
        # Deleting model 'Zephyr'
        db.delete_table('chat_zephyr')

        # Deleting model 'Subscription'
        db.delete_table('chat_subscription')

        # Deleting model 'Account'
        db.delete_table('chat_account')

        # Removing M2M table for field subscriptions on 'Account'
        db.delete_table('chat_account_subscriptions')


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
            'recipient': ('django.db.models.fields.CharField', [], {'max_length': '200'})
        },
        'chat.zephyr': {
            'Meta': {'object_name': 'Zephyr'},
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'dst': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['chat.Subscription']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {}),
            'sender': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'signature': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['chat']
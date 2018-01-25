# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2018-01-24 08:30
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_postmark_utils', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='message',
            name='body',
        ),
        migrations.RemoveField(
            model_name='message',
            name='content_type',
        ),
        migrations.RemoveField(
            model_name='message',
            name='encoding',
        ),
        migrations.RemoveField(
            model_name='message',
            name='raw_header',
        ),
        migrations.AddField(
            model_name='message',
            name='pickled_obj',
            field=models.BinaryField(blank=True, help_text='Pickled message object', unique=True, verbose_name='Pickled object'),
        ),
    ]
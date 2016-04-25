# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-04-21 21:09
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('elmcafiolo', '0004_auto_20160421_2104'),
    ]

    operations = [
        migrations.AlterField(
            model_name='job',
            name='transcoder',
            field=models.ForeignKey(blank=True, default='', on_delete=django.db.models.deletion.CASCADE, to='elmcafiolo.Transcoder'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='transcoder',
            name='slots',
            field=models.IntegerField(blank=True, help_text='Availables slots', null=True),
        ),
    ]
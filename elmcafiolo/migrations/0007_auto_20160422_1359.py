# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-04-22 13:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('elmcafiolo', '0006_auto_20160422_1358'),
    ]

    operations = [
        migrations.AlterField(
            model_name='job',
            name='job_id',
            field=models.IntegerField(blank=True, help_text='Transcoder job ID', null=True),
        ),
    ]
# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-07-29 04:31
from __future__ import unicode_literals

from django.db import migrations

def update_timeslot_day_index(apps, schema_editor):
    Timeslot = apps.get_model('sophia', 'Timeslot')
    for ts in Timeslot.objects.all():
        ts.day = str(int(ts.day) - 1)
        ts.save()

class Migration(migrations.Migration):

    dependencies = [
        ('sophia', '0008_change_day_field_on_timeslot'),
    ]

    operations = [
        migrations.RunPython(update_timeslot_day_index)
    ]

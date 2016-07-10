# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import ckeditor.fields


class Migration(migrations.Migration):

    dependencies = [
        ('sophia', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PageText',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('page_name', models.CharField(max_length=255)),
                ('text', ckeditor.fields.RichTextField()),
            ],
        ),
        migrations.AddField(
            model_name='testimonial',
            name='priority',
            field=models.BooleanField(default=False, help_text=b'Should this testimonial be prioritized                         to be displayed?'),
        ),
        migrations.AlterField(
            model_name='testimonial',
            name='text',
            field=ckeditor.fields.RichTextField(),
        ),
    ]

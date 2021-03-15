# Generated by Django 3.0.5 on 2021-03-10 08:57

import backend.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0021_auto_20210217_2319'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='avatar',
            name='image',
        ),
        migrations.AddField(
            model_name='avatar',
            name='v1',
            field=models.ImageField(blank=True, null=True, upload_to=backend.models.avatar_path_v1),
        ),
        migrations.AddField(
            model_name='avatar',
            name='v2',
            field=models.ImageField(blank=True, null=True, upload_to=backend.models.avatar_path_v2),
        ),
    ]
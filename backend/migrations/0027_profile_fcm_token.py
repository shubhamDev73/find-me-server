# Generated by Django 3.0.5 on 2021-03-21 16:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0026_auto_20210321_1923'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='fcm_token',
            field=models.CharField(blank=True, max_length=200),
        ),
    ]

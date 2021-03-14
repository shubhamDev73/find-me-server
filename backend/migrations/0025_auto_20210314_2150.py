# Generated by Django 3.0.5 on 2021-03-14 16:20

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0024_profile_last_questionnaire_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='connect',
            name='last_read_time1',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='connect',
            name='last_read_time2',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]

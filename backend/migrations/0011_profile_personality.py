# Generated by Django 3.0.5 on 2020-08-24 03:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0010_personalityquestionnaire'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='personality',
            field=models.CharField(default='000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000', max_length=120),
        ),
    ]
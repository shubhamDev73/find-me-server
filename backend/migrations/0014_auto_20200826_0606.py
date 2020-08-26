# Generated by Django 3.0.5 on 2020-08-26 00:36

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0013_auto_20200826_0310'),
    ]

    operations = [
        migrations.AlterField(
            model_name='personalityquestionnaire',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backend.Profile'),
        ),
        migrations.AlterField(
            model_name='userinterest',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='backend.Profile'),
        ),
    ]

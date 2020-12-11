# Generated by Django 3.0.5 on 2020-12-11 12:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0018_auto_20201211_1727'),
    ]

    operations = [
        migrations.CreateModel(
            name='Personality',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('trait', models.IntegerField(choices=[(0, 'E'), (1, 'N'), (2, 'A'), (3, 'C'), (4, 'O')], unique=True)),
                ('display_name', models.CharField(max_length=20)),
                ('description', models.TextField(blank=True)),
            ],
            options={
                'verbose_name_plural': 'personalities',
            },
        ),
    ]
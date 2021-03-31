# Generated by Django 3.0.5 on 2021-03-31 12:40

import backend.models
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0029_userinterest_last_change'),
    ]

    operations = [
        migrations.AddField(
            model_name='mood',
            name='icon',
            field=models.FileField(default='', upload_to=backend.models.mood_icon_path, validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['blp', 'bmp', 'dib', 'bufr', 'cur', 'pcx', 'dcx', 'dds', 'ps', 'eps', 'fit', 'fits', 'fli', 'flc', 'ftc', 'ftu', 'gbr', 'gif', 'grib', 'h5', 'hdf', 'png', 'apng', 'jp2', 'j2k', 'jpc', 'jpf', 'jpx', 'j2c', 'icns', 'ico', 'im', 'iim', 'tif', 'tiff', 'jfif', 'jpe', 'jpg', 'jpeg', 'mpg', 'mpeg', 'mpo', 'msp', 'palm', 'pcd', 'pdf', 'pxr', 'pbm', 'pgm', 'ppm', 'pnm', 'psd', 'bw', 'rgb', 'rgba', 'sgi', 'ras', 'tga', 'icb', 'vda', 'vst', 'webp', 'wmf', 'emf', 'xbm', 'xpm', 'svg'])]),
            preserve_default=False,
        ),
    ]

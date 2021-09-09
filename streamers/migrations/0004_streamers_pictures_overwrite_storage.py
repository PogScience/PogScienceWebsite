# Generated by Django 3.2.7 on 2021-09-08 22:41

from django.db import migrations, models
import pogscience.storage
import streamers.models


class Migration(migrations.Migration):

    dependencies = [
        ('streamers', '0003_default_streamers_live_to_false'),
    ]

    operations = [
        migrations.AlterField(
            model_name='streamer',
            name='profile_image',
            field=models.ImageField(blank=True, null=True, storage=pogscience.storage.OverwriteStorage(), upload_to=streamers.models.profile_image_upload_to, verbose_name='Image de profil'),
        ),
    ]

# Generated by Django 3.2.7 on 2021-09-09 13:31

from django.db import migrations, models
import pogscience.storage
import streamers.models


class Migration(migrations.Migration):

    dependencies = [
        ("streamers", "0004_streamers_pictures_overwrite_storage"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="streamer",
            options={"ordering": ["name", "twitch_login"]},
        ),
        migrations.AddField(
            model_name="streamer",
            name="background_image",
            field=models.ImageField(
                blank=True,
                null=True,
                storage=pogscience.storage.OverwriteStorage(),
                upload_to=streamers.models.background_image_upload_to,
                verbose_name="Image de fond",
            ),
        ),
        migrations.AlterField(
            model_name="streamer",
            name="profile_image",
            field=models.ImageField(
                blank=True,
                null=True,
                storage=pogscience.storage.OverwriteStorage(),
                upload_to=streamers.models.profile_image_upload_to,
                verbose_name="Image de profil",
            ),
        ),
    ]

# Generated by Django 3.2.7 on 2021-09-08 22:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("streamers", "0002_add_streamers_profile_picture_and_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="streamer",
            name="live",
            field=models.BooleanField(
                default=False,
                help_text="Est-iel en live actuellement ? Mis à jour automatiquement",
                verbose_name="Est en live actuellement",
            ),
        ),
    ]

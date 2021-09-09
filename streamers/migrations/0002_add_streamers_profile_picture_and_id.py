# Generated by Django 3.2.7 on 2021-09-08 22:22

from django.db import migrations, models
import streamers.models


class Migration(migrations.Migration):

    dependencies = [
        ('streamers', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='streamer',
            name='profile_image',
            field=models.ImageField(blank=True, null=True, upload_to=streamers.models.profile_image_upload_to, verbose_name='Image de profil'),
        ),
        migrations.AddField(
            model_name='streamer',
            name='twitch_id',
            field=models.PositiveBigIntegerField(default=0, verbose_name="L'identifiant numérique Twitch"),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='streamer',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='user',
            name='first_name',
            field=models.CharField(blank=True, max_length=150, verbose_name='first name'),
        ),
        migrations.AlterField(
            model_name='user',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]

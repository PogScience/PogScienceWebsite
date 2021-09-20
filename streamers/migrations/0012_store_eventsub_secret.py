# Generated by Django 3.2.7 on 2021-09-17 22:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("streamers", "0011_move_subscriptions_to_dedicated_model"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="eventsubsubscription",
            options={"verbose_name": "abonnement EventSub", "verbose_name_plural": "abonnements EventSub"},
        ),
        migrations.AlterModelOptions(
            name="streamer",
            options={
                "ordering": ["name", "twitch_login"],
                "verbose_name": "streamer",
                "verbose_name_plural": "streamers",
            },
        ),
        migrations.AddField(
            model_name="eventsubsubscription",
            name="secret",
            field=models.CharField(
                default="UNSET",
                help_text="Secret to authenticate the subscription requests from Twitch",
                max_length=100,
                verbose_name="subscription secret",
            ),
            preserve_default=False,
        ),
    ]
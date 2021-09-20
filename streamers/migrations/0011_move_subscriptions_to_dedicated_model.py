# Generated by Django 3.2.7 on 2021-09-17 15:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("streamers", "0010_add_eventsub_status"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="scheduledstream",
            options={"verbose_name": "Stream planifié", "verbose_name_plural": "Streams planifiés"},
        ),
        migrations.AlterModelOptions(
            name="streamer",
            options={
                "ordering": ["name", "twitch_login"],
                "verbose_name": "Streamer",
                "verbose_name_plural": "Streamers",
            },
        ),
        migrations.RemoveField(
            model_name="streamer",
            name="eventsub_subscription_active",
        ),
        migrations.AlterField(
            model_name="streamer",
            name="twitch_id",
            field=models.PositiveBigIntegerField(
                help_text="Utilisé pour récupérer les informations automatiquement",
                verbose_name="identifiant numérique Twitch",
            ),
        ),
        migrations.CreateModel(
            name="EventSubSubscription",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("type", models.CharField(max_length=100, verbose_name="subscription type")),
                ("uuid", models.UUIDField(verbose_name="subscription UUID")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("unsubscribed", "Non-souscrit"),
                            ("pending", "En attente"),
                            ("subscribed", "Souscrit"),
                        ],
                        default="unsubscribed",
                        max_length=12,
                        verbose_name="subscription status",
                    ),
                ),
                (
                    "last_seen",
                    models.DateTimeField(
                        blank=True,
                        help_text="When was the last request from Twitch received",
                        null=True,
                        verbose_name="last seen",
                    ),
                ),
                (
                    "streamer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="eventsub_subscriptions",
                        to="streamers.streamer",
                        verbose_name="Streamer",
                    ),
                ),
            ],
            options={
                "verbose_name": "Abonnement EventSub",
                "verbose_name_plural": "Abonnements EventSub",
            },
        ),
    ]
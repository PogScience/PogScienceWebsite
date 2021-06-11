from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    pass


class Streamer(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        verbose_name=_("Compte interne du streamer"),
        null=True,
        default=None,
    )

    name = models.CharField(
        verbose_name=_("Nom du streamer"),
        max_length=128,
        help_text=_("Le nom d'affichage du/de la streamer⋅euse"),
    )
    twitch_login = models.CharField(
        verbose_name=_("Le nom d'utilisateur Twitch exact"),
        max_length=64,
        help_text=_("Utilisé pour récupérer les informations automatiquement"),
    )
    description = models.CharField(
        verbose_name=_("Courte description"),
        max_length=512,
        help_text=_(
            "Une courte description affichée par exemple sur la page d'accueil"
        ),
    )
    long_description = models.TextField(
        verbose_name=_("Longue description"),
        help_text=_(
            "Description potentiellement très longue affichée sur la page du streamer ou de la streameuse"
        ),
    )

    live = models.BooleanField(
        verbose_name=_("Est en live actuellement"),
        help_text=_("Est-iel en live actuellement ? Mis à jour automatiquement"),
    )
    live_title = models.CharField(
        verbose_name=_("Titre du live"),
        max_length=140,
        blank=True,
        null=True,
        default=None,
        help_text=_(
            "Le titre du live en cours, récupéré automatiquement depuis Twitch"
        ),
    )
    live_game_name = models.CharField(
        verbose_name=_("Catégorie du stream"),
        max_length=140,
        blank=True,
        null=True,
        default=None,
        help_text=_(
            "La catégorie du live en cours, récupéré automatiquement depuis Twitch"
        ),
    )

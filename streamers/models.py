import os
from io import BytesIO

import requests
from django.core import files
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser

from pogscience.storage import OverwriteStorage


class User(AbstractUser):
    pass


def image_upload_to(folder):
    """
    Generates a function returning the filename to use for a streamer profile
    picture, or background image, or other. The image will be named against the
    streamer, in the given folder.
    
    :param folder: The folder where to store the image. 
    :return: A function for Django FileField's upload_to.
    """
    def _inner(instance, filename: str):
        """
        Used by Django, returns the filename to use for the streamers' profile
        pictures.
        """
        _, ext = os.path.splitext(filename)
        return f'twitch/{folder}/{instance.twitch_login}{ext}'
    return _inner


def profile_image_upload_to(*args, **kwargs):
    return image_upload_to("profile")(*args, **kwargs)


def background_image_upload_to(*args, **kwargs):
    return image_upload_to("background")(*args, **kwargs)


class Streamer(models.Model):
    class Meta:
        ordering = ['name', 'twitch_login']

    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        verbose_name=_("Compte interne du streamer"),
        null=True,
        blank=True,
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
    twitch_id = models.PositiveBigIntegerField(
        verbose_name=_("L'identifiant numérique Twitch")
    )
    description = models.CharField(
        verbose_name=_("Courte description"),
        max_length=512,
        help_text=_(
            "Une courte description affichée par exemple sur la page d'accueil"
        ),
        blank=True,
    )
    long_description = models.TextField(
        verbose_name=_("Longue description"),
        help_text=_(
            "Description potentiellement très longue affichée sur la page du streamer ou de la streameuse"
        ),
        blank=True,
    )
    profile_image = models.ImageField(
        verbose_name=_("Image de profil"),
        storage=OverwriteStorage(),
        upload_to=profile_image_upload_to,
        null=True,
        blank=True
    )
    background_image = models.ImageField(
        verbose_name=_("Image de fond"),
        storage=OverwriteStorage(),
        upload_to=background_image_upload_to,
        null=True,
        blank=True
    )

    live = models.BooleanField(
        verbose_name=_("Est en live actuellement"),
        help_text=_("Est-iel en live actuellement ? Mis à jour automatiquement"),
        default=False
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

    def __str__(self):
        return f"{self.name} – @{self.twitch_login}"

    def update_from_twitch_data(self, twitch_data):
        """
        Updates this instance using the data returned by Twitch. Does not save
        the instance.

        :param twitch_data: The Twitch data: https://dev.twitch.tv/docs/api/reference#get-users
        """
        self.name = twitch_data["display_name"]

        self.twitch_id = twitch_data["id"]
        self.twitch_login = twitch_data["login"]

        self.description = twitch_data["description"]

        def _download_and_store_image(key, field):
            if not twitch_data[key]:
                return

            res_image = requests.get(twitch_data[key])
            if not res_image.ok:
                return

            image = BytesIO()
            image.write(res_image.content)
            filename = f'image{os.path.splitext(twitch_data[key])[1]}'
            field.save(filename, files.File(image))

        _download_and_store_image("profile_image_url", self.profile_image)
        _download_and_store_image("offline_image_url", self.background_image)

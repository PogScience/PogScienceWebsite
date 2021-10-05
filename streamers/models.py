import binascii
import colorsys
import os
from datetime import timedelta
from io import BytesIO
from urllib.error import HTTPError
from uuid import UUID

import requests
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import AbstractUser
from django.core import files
from django.core.management.utils import get_random_secret_key
from django.db import models
from django.db.models import Q
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from pogscience.storage import OverwriteStorage
from pogscience.twitch import get_twitch_client
from streamers.utils import extract_main_colours, grouper


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
        return f"twitch/{folder}/{instance.twitch_login}{ext}"

    return _inner


def profile_image_upload_to(*args, **kwargs):
    return image_upload_to("profile")(*args, **kwargs)


def background_image_upload_to(*args, **kwargs):
    return image_upload_to("background")(*args, **kwargs)


def live_preview_image_upload_to(*args, **kwargs):
    return image_upload_to("live-preview")(*args, **kwargs)


class Streamer(models.Model):
    """
    A streamer, member of PogScience.
    """

    class Meta:
        verbose_name = _("streamer")
        verbose_name_plural = _("streamers")
        ordering = ["name", "twitch_login"]

    EVENTSUB_SUBSCRIPTIONS = ["stream.online", "stream.offline", "channel.update"]

    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        verbose_name=_("compte interne du streamer"),
        null=True,
        blank=True,
        default=None,
    )

    name = models.CharField(
        verbose_name=_("nom du streamer"),
        max_length=128,
        help_text=_("Le nom d'affichage du/de la streamer⋅euse"),
    )
    twitch_login = models.CharField(
        verbose_name=_("nom d'utilisateur Twitch"),
        max_length=64,
        help_text=_("Utilisé pour récupérer les informations automatiquement"),
    )
    twitch_id = models.PositiveBigIntegerField(
        verbose_name=_("identifiant numérique Twitch"),
        help_text=_("Utilisé pour récupérer les informations automatiquement"),
    )
    description = models.CharField(
        verbose_name=_("courte description"),
        max_length=512,
        help_text=_("Une courte description affichée par exemple sur la page d'accueil"),
        blank=True,
    )
    long_description = models.TextField(
        verbose_name=_("longue description"),
        help_text=_("Description potentiellement très longue affichée sur la page du streamer ou de la streameuse"),
        blank=True,
    )
    profile_image = models.ImageField(
        verbose_name=_("image de profil"),
        storage=OverwriteStorage(),
        upload_to=profile_image_upload_to,
        null=True,
        blank=True,
    )
    background_image = models.ImageField(
        verbose_name=_("image de fond"),
        storage=OverwriteStorage(),
        upload_to=background_image_upload_to,
        null=True,
        blank=True,
    )
    _colours = models.CharField(
        verbose_name=_("couleurs"),
        help_text=_(
            "Liste de trois couleurs principales à utiliser pour habiller ce/cette streamer/euse. Les valeurs "
            "sont stockées sous la forme d'une liste de nombres flottants, dont chaque triplet forme une "
            "couleur RGB."
        ),
        # max 7 chars per rgb value, three rgb tuples, and 8 comma separators
        max_length=71,  # 7*3*3 + 8
        blank=True,
        null=True,
        db_column="colours",
    )

    live = models.BooleanField(
        verbose_name=_("en live ?"),
        help_text=_("Est-iel en live actuellement ? Mis à jour automatiquement"),
        default=False,
    )
    live_title = models.CharField(
        verbose_name=_("titre du live"),
        max_length=140,
        blank=True,
        null=True,
        default=None,
        help_text=_("Le titre du live en cours, récupéré automatiquement depuis Twitch"),
    )
    live_game_name = models.CharField(
        verbose_name=_("catégorie du stream"),
        max_length=140,
        blank=True,
        null=True,
        default=None,
        help_text=_("La catégorie du live en cours, récupéré automatiquement depuis Twitch"),
    )
    live_started_at = models.DateTimeField(
        verbose_name=_("début du stream"),
        blank=True,
        null=True,
        default=None,
        help_text=_("L'heure de début du live en cours"),
    )
    live_preview = models.ImageField(
        verbose_name=_("aperçu du live"),
        storage=OverwriteStorage(),
        upload_to=live_preview_image_upload_to,
        null=True,
        blank=True,
    )
    live_spectators = models.PositiveIntegerField(
        verbose_name=_("spectateurs"),
        blank=True,
        null=True,
        default=None,
    )

    def __str__(self):
        return self.name

    @property
    def twitch_url(self):
        return f"https://twitch.tv/{self.twitch_login}"

    @property
    def duration(self):
        return timezone.now() - self.live_started_at if self.live_started_at else None

    @property
    def colours(self):
        return list(map(tuple, grouper(map(float, self._colours.split(",")), 3)))

    @colours.setter
    def colours(self, value):
        flat = [val for colour in value for val in colour]
        self._colours = ",".join(map(str, flat))

    @colours.deleter
    def colours(self):
        self._colours = None

    @property
    def colours_hex(self):
        return list(
            map(lambda colour: "#" + binascii.hexlify(bytearray(int(c) for c in colour)).decode("ascii"), self.colours)
        )

    @property
    def colours_hsl(self):
        def rgb_to_hsl(colour):
            h, l, s = colorsys.rgb_to_hls(*map(lambda c: c / 255.0, colour))
            return h * 360, s * 100, l * 100

        return list(map(rgb_to_hsl, self.colours))

    @staticmethod
    def _download_and_store_image(url, field):
        if not url:
            return

        res_image = requests.get(url)
        if not res_image.ok:
            return

        image = BytesIO()
        image.write(res_image.content)
        filename = f"image{os.path.splitext(url)[1]}"
        field.save(filename, files.File(image), save=False)

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

        self._download_and_store_image(twitch_data.get("profile_image_url"), self.profile_image)
        self._download_and_store_image(twitch_data.get("offline_image_url"), self.background_image)
        self.update_colours()

    def update_stream_from_twitch_data(self, twitch_data):
        """
        Updates the current stream using the data returned by Twitch. Does not
        save the instance.
        :param twitch_data: The Twitch data: https://dev.twitch.tv/docs/api/reference#get-streams
        """
        self.live_title = twitch_data["title"]
        self.live_game_name = twitch_data["game_name"]
        self.live_spectators = twitch_data["viewer_count"]

        thumbnail = (
            twitch_data["thumbnail_url"]
            .replace("{width}", str(settings.POG_PREVIEWS["WIDTH"]))
            .replace("{height}", str(settings.POG_PREVIEWS["HEIGHT"]))
        )

        self._download_and_store_image(thumbnail, self.live_preview)

    def update_stream(self):
        """
        Updates this streamer's current stream (if the streamer is live and
        Twitch returns a stream for it).
        """
        client = get_twitch_client()
        streams = client.get_streams(user_ids=[self.twitch_id])
        try:
            self.update_stream_from_twitch_data(streams[0])
        except IndexError:
            # The streamer is not live: Twitch returned nothing about its stream.
            pass

    def start_stream(self):
        """
        Starts the current stream, and store the start time of it for later use (see `end_stream`).
        Does not save the Streamer instance.
        """
        self.live = True
        self.live_started_at = timezone.now()

    def end_stream(self):
        """
        Ends the current stream, and mark any corresponding scheduled stream as “done”, so
        they wont show up on the homepage if the stream finished in advance.
        Does not save the Streamer instance.
        """
        self.live = False

        if self.live_started_at:
            ScheduledStream.objects.filter(
                streamer=self, start__lte=timezone.now(), end__gte=self.live_started_at
            ).update(done=True)
            self.live_started_at = None

    def update_colours(self):
        """
        Updates the streamer's main colors from its profile picture. Does not
        save the instance.
        """
        if not self.profile_image:
            return

        self.colours = extract_main_colours(self.profile_image.path, colours_count=3)

    def subscribe_to_eventsub(self):
        """
        Subscribes to EventSub subscriptions listed in `Streamer.EVENTSUB_SUBSCRIPTIONS`.

        :return: With event_type being a string containing the corresponding eventsub event type subscribed to, returns
        a list with, for each subscription:
        - (event_type, True) if a subscription was successfully created;
        - (event_type, False) if a subscription already existed for that event;
        - (event_type, e) with e being an HTTPError, if an error occurred.
        """
        client = get_twitch_client()
        result = []

        for event_type in self.EVENTSUB_SUBSCRIPTIONS:
            if EventSubSubscription.objects.filter(streamer=self, type=event_type).exists():
                result.append((event_type, False))
                continue

            try:
                secret = get_random_secret_key()
                sub = client.eventsub_subscribe(
                    event_type=event_type,
                    callback_url=f"https://{settings.HOST}{reverse('streamers:eventsub-ingest')}",
                    secret=secret,
                    event_condition={"broadcaster_user_id": str(self.twitch_id)},
                )[0]

                EventSubSubscription(
                    streamer=self,
                    type=sub["type"],
                    uuid=UUID(sub["id"]),
                    secret=secret,
                    status=EventSubSubscription.PENDING,
                ).save()

                result.append((event_type, True))

            except HTTPError as e:
                result.append((event_type, e))

        return result

    def unsubscribe_from_eventsub(self):
        """
        Unsubscribes from every known subscription for this streamer.

        :return: With event_type being a string containing the corresponding eventsub event type subscribed to, returns
        a list with, for each subscription:
        - (event_type, True) if the subscription was successfully removed;
        - (event_type, e) with e being an HTTPError, if an error occurred.
        """
        client = get_twitch_client()
        result = []

        for sub in EventSubSubscription.objects.filter(streamer=self):
            try:
                client.eventsub_delete_subscription(uuid=sub.uuid)
                sub.delete()
                result.append((sub.type, True))
            except HTTPError as e:
                result.append((sub.type, e))

        return result

    @classmethod
    def full_twitch_sync(cls):
        """Checks for every channel current live status, and updates every registered channel accordingly."""
        client = get_twitch_client()
        streams = client.get_streams(user_ids=[streamer.twitch_id for streamer in cls.objects.all()])
        online_streamers_ids = [int(stream["user_id"]) for stream in streams]

        # For lives with a stored start date, we don't alter it. But we add one for those who don't.
        cls.objects.filter(twitch_id__in=online_streamers_ids, live_started_at__isnull=True).update(
            live=True, live_started_at=timezone.now()
        )
        cls.objects.filter(twitch_id__in=online_streamers_ids, live_started_at__isnull=False).update(live=True)

        # For offline streams, we have to call the end_stream method for each of them, as this will mark as done
        # corresponding scheduled streams, if any.
        offline_streamers = list(cls.objects.filter(~Q(twitch_id__in=online_streamers_ids)))
        for streamer in offline_streamers:
            streamer.end_stream()
        cls.objects.bulk_update(offline_streamers, ["live", "live_started_at"])


@receiver(pre_save, sender=Streamer)
def update_stream_when_streamer_goes_live(sender, instance: Streamer, **kwargs):
    instance.update_stream()


class EventSubSubscription(models.Model):
    class Meta:
        verbose_name = _("abonnement EventSub")
        verbose_name_plural = _("abonnements EventSub")

    UNSUBSCRIBED = "unsubscribed"
    SUBSCRIBED = "subscribed"
    PENDING = "pending"
    STATUS_CHOICES = [
        (UNSUBSCRIBED, _("Non-souscrit")),
        (PENDING, _("En attente")),
        (SUBSCRIBED, _("Souscrit")),
    ]

    streamer = models.ForeignKey(
        Streamer,
        verbose_name=_("Streamer"),
        related_name="eventsub_subscriptions",
        on_delete=models.CASCADE,
    )

    type = models.CharField(
        verbose_name=_("subscription type"),
        max_length=100,
    )

    uuid = models.UUIDField(
        verbose_name=_("subscription UUID"),
    )

    secret = models.CharField(
        verbose_name=_("subscription secret"),
        help_text=_("Secret to authenticate the subscription requests from Twitch"),
        max_length=100,
    )

    status = models.CharField(
        verbose_name=_("subscription status"),
        max_length=12,
        choices=STATUS_CHOICES,
        default=UNSUBSCRIBED,
    )

    last_seen = models.DateTimeField(
        verbose_name=_("last seen"),
        help_text=_("When was the last request from Twitch received"),
        blank=True,
        null=True,
    )

    @property
    def last_seen_since(self) -> timedelta:
        return timezone.now() - self.last_seen

    def __str__(self):
        return f"EventSub subscription {self.type}"


class ScheduledStream(models.Model):
    """
    A streamer's planned stream, loaded from Twitch or Google Calendar.
    """

    class Meta:
        verbose_name = _("Stream planifié")
        verbose_name_plural = _("Streams planifiés")

    streamer = models.ForeignKey(
        Streamer,
        verbose_name=_("streamer ayant programmé le stream"),
        related_name="schedule",
        on_delete=models.CASCADE,
    )

    title = models.CharField(_("titre du stream programmé"), max_length=140)

    start = models.DateTimeField(_("heure de début prévue"))
    end = models.DateTimeField(_("heure de fin prévue"))

    category = models.CharField(_("catégorie du stream"), max_length=140, blank=True, null=True)

    weekly = models.BooleanField(_("hebdomadaire ?"))

    twitch_segment_id = models.CharField(
        _("identifiant interne du segment Twitch"),
        max_length=128,
        null=True,
        blank=True,
        editable=False,
    )

    google_calendar_event_id = models.CharField(
        _("identifiant interne de l'événement Google Calendar"), max_length=128, null=True, blank=True, editable=False
    )

    done = models.BooleanField(_("terminé ?"), default=False)

    @property
    @admin.display(description=_("Durée"))
    def duration(self):
        return self.end - self.start

    @property
    def now(self):
        return self.start < timezone.now() < self.end

    def __str__(self):
        return f"{self.title} ({self.streamer}, {self.start} → {self.end})"

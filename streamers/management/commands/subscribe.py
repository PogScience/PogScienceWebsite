from pprint import pprint
from uuid import UUID

import djclick as click
import requests

from django.conf import settings
from django.core.management.utils import get_random_secret_key
from django.db import transaction
from django.urls import reverse
from requests import HTTPError

from pogscience.twitch import TwitchHelix, get_twitch_client
from streamers.models import EventSubSubscription, Streamer


def subscribe_to(client: TwitchHelix, streamer: Streamer, event_type: str):
    """
    Initializes an EventSub subscription at Twitch, and returns the (unsaved yet)
    EventSubSubscription model instance. If a subscription already exist, we don't
    re-sub.

    :param client: The Twitch client.
    :param streamer: The streamer to create the subscription for.
    :param event_type: The event to subscribe to.
    :return: The EventSubSubscription (unsaved), or None if a subscription already existed.
    """
    if EventSubSubscription.objects.filter(streamer=streamer, type=event_type).exists():
        return None

    secret = get_random_secret_key()
    sub = client.eventsub_subscribe(
        event_type=event_type,
        callback_url=f"https://{settings.HOST}{reverse('streamers:eventsub-ingest')}",
        secret=secret,
        event_condition={"broadcaster_user_id": str(streamer.twitch_id)},
    )[0]

    return EventSubSubscription(
        streamer=streamer,
        type=sub["type"],
        uuid=UUID(sub["id"]),
        secret=secret,
        status=EventSubSubscription.PENDING,
    )


@click.command()
@transaction.atomic
def command():
    """
    Subscribes or re-subscribes to the Twitch Webhooks for streams updates
    notifications.
    """
    client = get_twitch_client()
    subs = []

    for streamer in Streamer.objects.all():
        click.secho(f"Subscribing to {streamer.name} streams webhooks...", fg="cyan", bold=True)
        for event_type in ["stream.online", "stream.offline", "channel.update"]:
            click.echo(f"* {event_type}…", nl=False)
            try:
                sub = subscribe_to(client, streamer, event_type)
                if sub:
                    click.secho(" OK", fg="green", bold=True)
                    subs.append(sub)
                else:
                    click.secho(" ALREADY SUBSCRIBED", fg="yellow", bold=True)
            except HTTPError as e:
                click.echo(click.style(" ERR", fg="red", bold=True) + f" {e}")

    click.echo("Saving subscriptions...", nl=False)
    EventSubSubscription.objects.bulk_create(subs)
    click.secho(" OK", fg="green", bold=True)

import djclick as click

from django.db import transaction
from requests import HTTPError

from pogscience.twitch import get_twitch_client
from streamers.models import EventSubSubscription, Streamer


@click.command()
@click.argument("streamer", nargs=-1)
@transaction.atomic
def command(streamer):
    """
    Unsubscribes from the Twitch EventSub webhooks for streams updates
    notifications, for the given streamers, or all streamers if not provided.
    """
    client = get_twitch_client()
    deleted_subs = []

    if streamer:
        streamers = Streamer.objects.filter(twitch_login__in=streamer)
    else:
        streamers = Streamer.objects.all()

    for streamer in streamers:
        click.secho(f"Unsubscribing from {streamer.name} streams webhooks...", fg="cyan", bold=True)
        for sub in EventSubSubscription.objects.filter(streamer=streamer):
            click.echo(f"* {sub.type}...", nl=False)
            try:
                client.eventsub_delete_subscription(uuid=sub.uuid)
                deleted_subs.append(sub)
                click.secho(" OK", fg="green", bold=True)
            except HTTPError as e:
                click.echo(click.style(" ERR", fg="red", bold=True) + f" {e}")

    click.echo("Saving subscriptions...", nl=False)
    for sub in deleted_subs:
        sub.delete()
    click.secho(" OK", fg="green", bold=True)

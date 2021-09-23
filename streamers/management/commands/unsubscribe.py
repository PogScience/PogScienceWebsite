import djclick as click
from django.db import transaction

from streamers.models import Streamer


@click.command()
@click.argument("streamer", nargs=-1)
@transaction.atomic
def command(streamer):
    """
    Unsubscribes from the Twitch EventSub webhooks for streams updates
    notifications, for the given streamers, or all streamers if not provided.
    """
    if streamer:
        streamers = Streamer.objects.filter(twitch_login__in=streamer)
    else:
        streamers = Streamer.objects.all()

    for streamer in streamers:
        click.secho(f"Unsubscribing from {streamer.name} streams webhooks...", fg="cyan", bold=True)
        for event_type, deleted in streamer.unsubscribe_from_eventsub():
            click.echo(f"* {event_type}...", nl=False)
            if deleted is True:
                click.secho(" OK", fg="green", bold=True)
            else:
                click.echo(click.style(" ERR", fg="red", bold=True) + f" {deleted}")

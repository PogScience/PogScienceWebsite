import djclick as click
from django.db import transaction

from streamers.models import Streamer


@click.command()
@transaction.atomic
def command():
    """
    Subscribes or re-subscribes to the Twitch Webhooks for streams updates
    notifications.
    """
    for streamer in Streamer.objects.all():
        click.secho(f"Subscribing to {streamer.name} streams webhooks...", fg="cyan", bold=True)
        for event_type, created in streamer.subscribe_to_eventsub():
            click.echo(f"* {event_type}...", nl=False)
            if created is True:
                click.secho(" OK", fg="green", bold=True)
            elif created is False:
                click.secho(" ALREADY SUBSCRIBED", fg="yellow", bold=True)
            else:
                click.echo(click.style(" ERR", fg="red", bold=True) + f" {created}")

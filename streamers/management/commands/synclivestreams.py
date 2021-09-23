import djclick as click
from django.db import transaction

from pogscience.twitch import get_twitch_client
from streamers.models import Streamer


@click.command()
@click.option("--full", is_flag=True, help="Checks for online/offline status for every streamer, too.")
@transaction.atomic
def command(full):
    """
    Updates the live stream preview (and stream data) for live streamers.
    If no one is live, outputs nothing.
    """
    client = get_twitch_client()

    if full:
        click.secho(f"Checking for streams status (--full)...", fg="cyan", bold=True, nl=False)
        Streamer.full_twitch_sync()
        click.secho(" OK", fg="green", bold=True)

    streamers = {str(streamer.twitch_id): streamer for streamer in Streamer.objects.filter(live=True)}
    if not streamers:
        return

    streams = client.get_streams(user_ids=streamers.keys())

    for stream in streams:
        click.secho(f"Updating {stream['user_name']}'s stream preview and data...", fg="cyan", bold=True, nl=False)

        try:
            streamer: Streamer = streamers[stream["user_id"]]
            if not streamer:
                raise ValueError(f"Streamer {stream['user_name']} returned by Twitch but unknown to us.")
            streamer.update_stream_from_twitch_data(stream)
            streamer.save()
            click.secho(" OK", fg="green", bold=True)
        except Exception as e:
            click.echo(click.style(" ERR", fg="red", bold=True) + f" {e}")

from streamers.models import Streamer


def associate_streamer(details, user=None, **kwargs):
    if user:
        try:
            streamer = Streamer.objects.get(twitch_login=details.get("username"))
            streamer.user = user
            streamer.save()
        except Streamer.DoesNotExist:
            pass

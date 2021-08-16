from django.conf import settings


def twitch(request):
    return {"twitch": {"enabled": settings.POG_TWITCH_ENABLED}}

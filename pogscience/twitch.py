from django.conf import settings
from twitch import TwitchHelix

_client = TwitchHelix(
    client_id=settings.SOCIAL_AUTH_TWITCH_KEY,
    client_secret=settings.SOCIAL_AUTH_TWITCH_SECRET,
    scopes=[],
)


def get_twitch_client():
    """
    Returns a configured Twitch Helix client, with a valid access token.
    """
    if not _client._oauth_token:
        _client.get_oauth()
    return _client

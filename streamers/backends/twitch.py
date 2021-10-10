from social_core.backends.twitch import TwitchOAuth2 as PSATwitchOAuth2
from django.conf import settings


class TwitchOAuth2(PSATwitchOAuth2):
    """
    The builtin Twitch backend was obsolete (using the v5 API no longer
    supported), hence this updated version.
    """

    ID_KEY = "id"
    DEFAULT_SCOPE = ["user:read:email", "chat:read", "chat:edit", "channel_editor"]
    STATE_PARAMETER = "state"

    def get_user_details(self, response):
        return {
            "username": response.get("login"),
            "email": response.get("email"),
            "first_name": response.get("display_name"),
            "last_name": "",
        }

    def user_data(self, access_token, *args, **kwargs):
        return self.get_json(
            "https://api.twitch.tv/helix/users",
            headers={
                "Client-Id": settings.SOCIAL_AUTH_TWITCH_KEY,
                "Authorization": f"Bearer {access_token}",
            },
        )["data"][0]

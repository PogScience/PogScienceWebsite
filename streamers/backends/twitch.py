from social_core.backends.twitch import TwitchOAuth2 as PSATwitchOAuth2


class TwitchOAuth2(PSATwitchOAuth2):
    """
    The builtin Twitch backend was obsolete (using the v5 API no longer
    supported), hence this updated version.
    """

    DEFAULT_SCOPE = ["user:read:email", "chat:read", "chat:edit", "channel_editor"]
    STATE_PARAMETER = "state"
    EXTRA_DATA = [
        ("access_token", "access_token"),
        ("refresh_token", "refresh_token"),
        ("expires_in", "expires"),
    ]

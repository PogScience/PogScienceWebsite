import socket
import ssl

from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework import views
from rest_framework.request import Request
from rest_framework.response import Response
from social_django.models import UserSocialAuth
from social_django.utils import load_strategy

from streamers.backends.twitch import TwitchOAuth2


def send_irc_message(sock: socket.socket, message: str):
    """
    Sends a IRC message over the given socket. Line breaks are appended and the
    string is encoded to bytes.

    :param sock: The socket.
    :param message: The message.
    """
    sock.send(bytes(message + "\r\n", "UTF-8"))


class RaidAPIView(LoginRequiredMixin, views.APIView):
    def post(self, request: Request, **kwargs):
        social: UserSocialAuth = request.user.social_auth.get(provider="twitch")
        if not social:
            raise RuntimeError(f"OAuth social data missing for user {request.user.username}")

        token = social.get_access_token(load_strategy(request))

        context = ssl.create_default_context()
        twitch_irc_host = "irc.chat.twitch.tv", 6697

        with socket.create_connection(twitch_irc_host) as sock:
            with context.wrap_socket(sock, server_hostname=twitch_irc_host[0]) as ssock:
                # Required to be able to send Twitch commands
                send_irc_message(ssock, "CAP REQ :twitch.tv/commands")

                # Authenticates to Twitch IRC
                send_irc_message(ssock, f"PASS oauth:{token}")
                send_irc_message(ssock, f"NICK {request.user.username}")
                send_irc_message(ssock, f"USER {request.user.username} 8 * :{request.user.username}")

                # Joins the stream chat's channel
                send_irc_message(ssock, f"JOIN #{request.user.username}")

                # Sends the /raid command
                send_irc_message(ssock, f"PRIVMSG #{request.user.username} :/raid {self.kwargs['twitch_login']}")

        return Response(status=204)

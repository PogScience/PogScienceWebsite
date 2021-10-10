import socket
import ssl

from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework import views
from rest_framework.request import Request
from rest_framework.response import Response


class RaidAPIView(LoginRequiredMixin, views.APIView):
    def send(self, sock: socket.socket, message: str):
        sock.send(bytes(message + "\r\n", "UTF-8"))

    def post(self, request: Request, **kwargs):
        social = request.user.social_auth.get(provider="twitch")
        if not social:
            raise RuntimeError(f"OAuth social data missing for user {request.user.username}")

        token = social.extra_data["access_token"]
        context = ssl.create_default_context()
        twitch_irc_host = "irc.chat.twitch.tv", 6697

        with socket.create_connection(twitch_irc_host) as sock:
            with context.wrap_socket(sock, server_hostname=twitch_irc_host[0]) as ssock:
                self.send(ssock, "CAP REQ :twitch.tv/commands")
                self.send(ssock, f"PASS oauth:{token}")
                self.send(ssock, f"NICK {request.user.username}")
                self.send(ssock, f"USER {request.user.username} 8 * :{request.user.username}")
                self.send(ssock, f"JOIN #{request.user.username}")
                self.send(ssock, f"PRIVMSG #{request.user.username} :/raid {self.kwargs['twitch_login']}")

        return Response(status=204)

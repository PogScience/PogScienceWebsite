import hashlib
import hmac
import json
import typing
from http import HTTPStatus
from uuid import UUID

from django.http import Http404, HttpRequest, HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from streamers.models import EventSubSubscription


# Twitch will not send a CSRF cookie, obviously. Request authenticity
# is checked differently, with the eventsub secret.
@method_decorator(csrf_exempt, name="dispatch")
class EventSubIngestView(View):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.request: typing.Optional[HttpRequest] = None
        self.payload: typing.Optional[dict] = None
        self.sub: typing.Optional[EventSubSubscription] = None
        self.event: typing.Optional[dict] = None

    def check_signature(self) -> bool:
        """
        Checks the request signature to ensure this request is legitimate.
        :return: True if the signature is valid.
        """
        headers = self.request.headers
        expected_signature = headers["Twitch-Eventsub-Message-Signature"]

        hmac_message = (
            headers["Twitch-Eventsub-Message-Id"]
            + headers["Twitch-Eventsub-Message-Timestamp"]
            + self.request.body.decode("utf-8")
        )
        signature = (
            hmac.new(key=bytes(self.sub.secret, "utf-8"), msg=bytes(hmac_message, "utf-8"), digestmod=hashlib.sha256)
            .hexdigest()
            .lower()
        )

        return expected_signature == f"sha256={signature}"

    def post(self, request: HttpRequest) -> HttpResponse:
        self.request = request
        self.payload = json.loads(request.body)

        try:
            self.sub = EventSubSubscription.objects.select_related("streamer").get(
                uuid=UUID(self.payload["subscription"]["id"])
            )
        except EventSubSubscription.DoesNotExist:
            raise Http404(f"Unknown eventsub subscription with UUID {self.payload['subscription']['id']}")

        if not self.check_signature():
            return HttpResponseForbidden("Invalid signature")

        self.sub.last_seen = timezone.now()

        status = self.payload["subscription"]["status"]
        handlers = {
            "webhook_callback_verification_pending": self.verification,
            "enabled": self.notification,
            "authorization_revoked": self.revocation,
        }

        response = handlers.get(status, self.bad_request)()

        self.sub.save()
        return response or HttpResponse(status=HTTPStatus.NOT_IMPLEMENTED)

    def verification(self) -> HttpResponse:
        """Handles the Twitch EventSub verification request."""
        self.sub.status = EventSubSubscription.SUBSCRIBED

        return HttpResponse(self.payload["challenge"])

    def notification(self) -> HttpResponse:
        """Handles the Twitch EventSub notifications requests."""
        self.event = self.payload["event"]

        event_type = self.payload["subscription"]["type"]
        handlers = {
            "channel.update": self.notification_update,
            "stream.online": self.notification_online,
            "stream.offline": self.notification_offline,
        }

        return handlers.get(event_type, lambda: None)()

    def notification_update(self) -> HttpResponse:
        streamer = self.sub.streamer
        streamer.live_title = self.event["title"]
        streamer.live_game_name = self.event["category_name"] if "category_name" in self.event else None
        streamer.save()

        return HttpResponse(status=HTTPStatus.NO_CONTENT)

    def notification_online(self) -> HttpResponse:
        streamer = self.sub.streamer
        streamer.start_stream()
        streamer.save()

        return HttpResponse(status=HTTPStatus.NO_CONTENT)

    def notification_offline(self) -> HttpResponse:
        streamer = self.sub.streamer
        streamer.end_stream()
        streamer.save()

        return HttpResponse(status=HTTPStatus.NO_CONTENT)

    def revocation(self) -> HttpResponse:
        """Handles the Twitch EventSub revocation requests. We re-subscribe immediately. Sorry… not sorry."""
        self.sub.delete()
        self.sub.streamer.subscribe_to_eventsub()
        return HttpResponse(status=HTTPStatus.NO_CONTENT)

    def bad_request(self) -> HttpResponse:
        """Handles unexpected requests coming from Twitch."""
        return HttpResponseBadRequest(
            f"Unknown status {self.payload['subscription']['status']} from Twitch notification for subscription "
            f"{self.sub.uuid}"
        )

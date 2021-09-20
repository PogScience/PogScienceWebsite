import datetime
from pprint import pprint
from urllib.parse import urljoin

import pytz
import requests
from django.conf import settings
from django.utils import timezone
from requests import codes
from twitch import TwitchHelix as TwitchHelixOriginal
from twitch.constants import BASE_HELIX_URL
from twitch.exceptions import TwitchAttributeException
from twitch.helix.base import APICursor, TwitchAPIMixin
from twitch.resources import TwitchObject


class Schedule(TwitchObject):
    pass


class EventSubSubscriptionCreated(TwitchObject):
    pass


class ScheduleAPICursor(APICursor):
    """
    The API response is not of the same format for schedule calls.
    """

    def __init__(self, client_id, path, resource, oauth_token=None, cursor=None, params=None):
        self._last_page = False
        super(ScheduleAPICursor, self).__init__(client_id, path, resource, oauth_token, cursor, params)

    def next_page(self):
        if self._cursor:
            self._params["after"] = self._cursor
        elif self._last_page:
            return None

        response = self._request_get(self._path, params=self._params)

        if response["data"]["segments"] is None:
            return None

        self._queue = [self._resource.construct_from(data) for data in response["data"]["segments"]]
        self._cursor = response["pagination"].get("cursor")
        self._total = response.get("total")

        if not self._cursor:
            self._last_page = True

        return self._queue


class APIEventSub(TwitchAPIMixin):
    def __init__(self, client_id, path, resource=None, oauth_token=None, params=None):
        super(APIEventSub, self).__init__()
        self._path = path
        self._resource = resource
        self._client_id = client_id
        self._oauth_token = oauth_token
        self._params = params

        self._url = urljoin(BASE_HELIX_URL, path)
        self._headers = self._get_request_headers()

    def _rate_limit_exceeded(self):
        remaining = self._response.headers.get("Ratelimit-Remaining")
        if remaining:
            self._rate_limit_remaining = int(remaining)

        reset = self._response.headers.get("Ratelimit-Reset")
        if reset:
            self._rate_limit_resets.add(int(reset))

        return self._response.status_code == codes.TOO_MANY_REQUESTS

    def _request_post(self, path, params=None):
        self._headers["Content-Type"] = "application/json"

        self._wait_for_rate_limit_reset()
        self._response = requests.post(self._url, json=params, headers=self._headers)

        # If status code is 429, re-run _request_post which will wait for the appropriate time
        # to obey the rate limit
        if self._rate_limit_exceeded():
            return self._request_post(path, params=params)

        self._response.raise_for_status()
        return self._response.json()

    def post(self):
        response = self._request_post(self._path, params=self._params)
        return response["data"]
        # skipped for now as the current implementation does not support dates with high
        # precision, as returned by the new EventSub API.
        # return [self._resource.construct_from(data) for data in response["data"]]

    def _request_delete(self, path, params=None):
        self._wait_for_rate_limit_reset()
        self._response = requests.delete(self._url, params=params, headers=self._headers)

        # If status code is 429, re-run _request_post which will wait for the appropriate time
        # to obey the rate limit
        if self._rate_limit_exceeded():
            return self._request_delete(path, params=params)

        self._response.raise_for_status()
        return self._response

    def delete(self):
        return self._request_delete(self._path, params=self._params)


class TwitchHelix(TwitchHelixOriginal):
    """
    A Twitch client to connect to the Twitch Helix API. Implements some new APIs
    to extend the `twitch` lib API.
    """

    @property
    def has_oauth(self):
        return self._oauth_token is not None

    def get_schedule(
        self,
        broadcaster_id,
        segments_ids=None,
        start_time: datetime.datetime = None,
        tz=None,
        page_size=20,
        after=None,
    ):
        """
        Loads the broadcaster's schedule.

        :param broadcaster_id: The broadcaster Twitch ID.
        :param segments_ids: The ID of the stream segment to return (maximum 100).
        :param start_time: A date to start returning stream segments from. If not
                           specified, the current date and time is used.
        :param tz: A pytz timezone.
                   This is recommended to ensure stream segments are returned for
                   the correct week. If not specified, GMT is used.
        :param page_size: Maximum number of stream segments to return.
        :param after: Cursor for forward pagination: tells the server where to start
                      fetching the next set of results in a multi-page response.
                      The cursor value specified here is from the pagination response
                      field of a prior query.

        :return: APICursor containing broadcaster schedule segments; see the structure
                 in the Twitch docs.
                 https://dev.twitch.tv/docs/api/reference#get-channel-stream-schedule
        """
        if page_size > 100:
            raise TwitchAttributeException("Maximum number of objects to return is 100")

        if tz is None:
            tz = pytz.UTC

        if start_time is not None:
            if isinstance(start_time, datetime.datetime) and not timezone.is_aware(start_time):
                start_time = timezone.make_aware(start_time, tz)
            elif isinstance(start_time, str):
                start_time = timezone.make_aware(datetime.datetime.fromisoformat(start_time), tz)

        params = {
            "broadcaster_id": broadcaster_id,
            "id": segments_ids,
            "start_time": start_time.toisoformat() if start_time is not None else None,
            "utc_offset": tz.utcoffset(pytz.UTC).seconds // 60,
            "after": after,
            "first": page_size,
        }

        return ScheduleAPICursor(
            client_id=self._client_id,
            oauth_token=self._oauth_token,
            path="schedule",
            resource=Schedule,
            params=params,
        )

    def eventsub_subscribe(
        self, event_type: str, callback_url: str, secret: str, event_condition=None, event_version="1"
    ):
        """
        Subscribes or unsubscribes to/from a Twitch EventSub. This is only the first subscription step;
        you need to implement the callback itself and a confirmation callback too.

        To renew an existing subscription, call this with the same arguments.

        All topics require an authorization token. Authorization requirements are based on the topic supplied; see the
        reference for each topic.

        Guide: https://dev.twitch.tv/docs/api/webhooks-guide
        Reference: https://dev.twitch.tv/docs/api/webhooks-reference/

        :param event_type: The topic URL, as specified in the Twitch docs. The first part of the URL
                      (https://api.twitch.tv/helix/) is optional.
                      See: https://dev.twitch.tv/docs/api/webhooks-reference/#subscribe-tounsubscribe-from-events
        :param callback_url: The URL Twitch will call when the event specified in `topic` occurs.
        :param secret: A secret to check the Twitch callbacks are authentic.
        :param event_condition: Subscription-specific parameters.
        :param event_version: The subscription type version: always 1 as for now.
        :return: The API response, that should be either a 201 Accepted if parameters are good, or 400 Bad Request else,
                 with empty body. The real subscription result will be sent to the callback URL (see the above guide).
        """
        if len(secret) < 10 or len(secret) > 100:
            raise ValueError("Subscriptions secrets must be between 10 and 100 characters")

        if not callback_url.lower().startswith("https:"):
            raise ValueError("The callback URL must use HTTPS and port 443.")

        params = {
            "type": event_type,
            "version": event_version,
            "condition": event_condition,
            "transport": {
                "method": "webhook",
                "callback": callback_url,
                "secret": secret,
            },
        }

        return APIEventSub(
            client_id=self._client_id,
            oauth_token=self._oauth_token,
            path="eventsub/subscriptions",
            resource=EventSubSubscriptionCreated,
            params=params,
        ).post()

    def eventsub_delete_subscription(self, uuid):
        """
        Deletes a subscription.

        :param uuid: The subscription's UUID.
        :return: The deletion response.
        """
        return APIEventSub(
            client_id=self._client_id,
            oauth_token=self._oauth_token,
            path="eventsub/subscriptions",
            params={"id": str(uuid)},
        ).delete()


_client = TwitchHelix(
    client_id=settings.SOCIAL_AUTH_TWITCH_KEY,
    client_secret=settings.SOCIAL_AUTH_TWITCH_SECRET,
    scopes=[],
)


def get_twitch_client():
    """
    Returns a configured Twitch Helix client, with a valid access token.
    """
    if not _client.has_oauth:
        _client.get_oauth()
    return _client

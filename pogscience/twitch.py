import datetime

import pytz
from django.conf import settings
from django.utils import timezone
from twitch import TwitchHelix as TwitchHelixOriginal
from twitch.exceptions import TwitchAttributeException
from twitch.helix.base import APICursor
from twitch.resources import TwitchObject


class Schedule(TwitchObject):
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


class TwitchHelix(TwitchHelixOriginal):
    """
    A Twitch client to connect to the Twitch Helix API. Implements some new APIs
    to extend the `twitch` lib API.
    """

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

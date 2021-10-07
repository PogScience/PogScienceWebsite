from django.urls import path

from streamers.views.eventsub import EventSubIngestView
from streamers.views.public import CalendarView, HomeView
from streamers.views.api import (
    LiveAndUpcomingAPIView,
    ScheduledStreamsAPIView,
    StreamersResourcesAPIView,
)

app_name = "streamers"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("calendrier", CalendarView.as_view(), name="calendar"),
    path("api/live-and-upcoming", LiveAndUpcomingAPIView.as_view(), name="api-live-upcoming"),
    path("api/scheduled", ScheduledStreamsAPIView.as_view(), name="api-scheduled"),
    path("api/streamers-resources", StreamersResourcesAPIView.as_view(), name="api-streamers-resources"),
    path("twitch/eventsub/ingest", EventSubIngestView.as_view(), name="eventsub-ingest"),
]

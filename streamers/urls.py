from django.urls import path

from streamers.views.eventsub import EventSubIngestView
from streamers.views.public import HomeLiveAndUpcomingPartView, HomeView

app_name = "streamers"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("partials/live-and-upcoming", HomeLiveAndUpcomingPartView.as_view(), name="home-part-live-upcoming"),
    path("twitch/eventsub/ingest", EventSubIngestView.as_view(), name="eventsub-ingest"),
]

from django.urls import path

from streamers.views.eventsub import EventSubIngestView
from streamers.views.public import HomeView

app_name = "streamers"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("twitch/eventsub/ingest", EventSubIngestView.as_view(), name="eventsub-ingest"),
]

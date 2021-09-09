from django.urls import path

from administration.views import AddStreamersView, IndexView, StreamersView, UpdateStreamersFromTwitch

app_name = "administration"

urlpatterns = [
    path("", IndexView.as_view(), name="index"),

    path("streamers/", StreamersView.as_view(), name="streamers"),
    path("streamers/add", AddStreamersView.as_view(), name="add-streamers"),
    path("streamers/twitch-update", UpdateStreamersFromTwitch.as_view(), name="update-streamers"),

    path("streamers/p/list", StreamersView.as_view(partial=True), name="streamers-partials-list"),
]

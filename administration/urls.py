from django.urls import path

from administration.views import AddStreamersView, IndexView, StreamersView

app_name = "administration"

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("streamers/", StreamersView.as_view(), name="streamers"),
    path("streamers/add", AddStreamersView.as_view(), name="add-streamers"),
]

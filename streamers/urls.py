from django.urls import path

from streamers.views import HomeView

app_name = "streamers"

urlpatterns = [path("", HomeView.as_view(), name="home")]

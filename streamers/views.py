from django.shortcuts import render
from django.views.generic import TemplateView
from django.conf import settings

from streamers.models import Streamer


class HomeView(TemplateView):
    template_name = "home.html"
    extra_context = {"streamers": Streamer.objects.all()}

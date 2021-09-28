import random

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from django.views.generic import TemplateView

from streamers.models import Streamer


# vary_on_cookie ensures the cache is never shared between users
@method_decorator([cache_page(3600), vary_on_cookie], name="dispatch")
class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self):
        context = super(HomeView, self).get_context_data()

        streamers = list(Streamer.objects.all())
        random.shuffle(streamers)
        context["streamers"] = streamers

        return context


class CalendarView(TemplateView):
    template_name = "calendar.html"

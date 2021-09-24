import random

from django.db.models import OuterRef, Subquery
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from django.views.generic import TemplateView

from streamers.models import ScheduledStream, Streamer


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


@method_decorator(cache_page(30), name="dispatch")
class HomeLiveAndUpcomingPartView(TemplateView):
    template_name = "live-and-upcoming.html"

    def get_context_data(self):
        now = timezone.now()

        context = super(HomeLiveAndUpcomingPartView, self).get_context_data()

        # We want scheduled stream that were not started yet (i.e.
        # the corresponding streamer is not live) and where the *end* time
        # is in the future (so streams starting late are still displayed).
        context["scheduled"] = (
            ScheduledStream.objects.filter(streamer__live=False, end__gte=now)
            .prefetch_related("streamer")
            .order_by("start")[:4]
        )

        # We try to associate live streamers with the corresponding planned stream, so we can display
        # the end time.
        context["live_streamers"] = Streamer.objects.filter(live=True).annotate(
            live_end=Subquery(
                ScheduledStream.objects.filter(streamer=OuterRef("pk"), start__lte=now, end__gte=now)
                .order_by("start")
                .values("end")[:1]
            )
        )

        context["all_spectators_count"] = sum(
            [streamer.live_spectators for streamer in context["live_streamers"] if streamer.live_spectators]
        )

        return context

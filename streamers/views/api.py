import dateutil.parser as dp

from django.db.models import OuterRef, Subquery
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.generic import TemplateView
from rest_framework import generics, views, viewsets
from rest_framework.response import Response

from streamers.models import ScheduledStream, Streamer
from streamers.serializers import (
    LiveAndScheduled,
    LiveAndScheduledSerializer,
    ScheduledStreamFullCalendarSerializer,
    StreamerResourceFullCalendarSerializer,
)


@method_decorator(cache_page(30), name="dispatch")
class LiveAndUpcomingAPIView(views.APIView):
    def get(self, request, **kwargs):
        now = timezone.now()
        live_and_upcoming = LiveAndScheduled(
            # We try to associate live streamers with the corresponding planned
            # stream, so we can display the end time.
            live=Streamer.objects.filter(live=True).annotate(
                live_end=Subquery(
                    ScheduledStream.objects.filter(streamer=OuterRef("pk"), start__lte=now, end__gte=now)
                    .order_by("start")
                    .values("end")[:1]
                )
            ),
            # We want scheduled stream that were not started yet (i.e.
            # the corresponding streamer is not live) and where the *end* time
            # is in the future (so streams starting late are still displayed).
            scheduled=(
                ScheduledStream.objects.filter(streamer__live=False, end__gte=now, done=False)
                .prefetch_related("streamer")
                .order_by("start")[:4]
            ),
        )

        serialized = LiveAndScheduledSerializer(live_and_upcoming)
        return Response(serialized.data)


@method_decorator(cache_page(300), name="list")
class ScheduledStreamsAPIView(generics.ListAPIView):
    serializer_class = ScheduledStreamFullCalendarSerializer

    def get_queryset(self):
        queryset = ScheduledStream.objects.all().order_by("start")
        start = self.request.query_params.get("start")
        end = self.request.query_params.get("end")

        try:
            start = dp.parse(start)
            queryset = queryset.filter(end__gte=start)
        except (TypeError, dp.ParserError):
            queryset = queryset.filter(end__gte=timezone.now())

        try:
            end = dp.parse(end)
            queryset = queryset.filter(start__lte=end)
        except (TypeError, dp.ParserError):
            pass

        return queryset


@method_decorator(cache_page(300), name="list")
class StreamersResourcesAPIView(generics.ListAPIView):
    queryset = Streamer.objects.all()
    serializer_class = StreamerResourceFullCalendarSerializer

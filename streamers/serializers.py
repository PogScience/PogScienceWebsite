from collections import namedtuple

from rest_framework import serializers

from streamers.models import Streamer, ScheduledStream


class StreamerSerializer(serializers.ModelSerializer):
    # colours_hsl = serializers.ListFeld()
    live_end = serializers.DateTimeField(required=False)

    class Meta:
        model = Streamer
        fields = [
            "name",
            "twitch_login",
            "twitch_url",
            "description",
            "profile_image",
            "colours_hsl",
            "colours_hsl_css",
            "live",
            "live_title",
            "live_game_name",
            "live_started_at",
            "live_preview",
            "live_spectators",
            "live_end",
            "live_duration",
        ]


class ScheduledStreamSerializer(serializers.ModelSerializer):
    streamer = StreamerSerializer(read_only=True)

    class Meta:
        model = ScheduledStream
        fields = ["pk", "streamer", "title", "start", "end", "category", "now", "weekly"]


class ScheduledStreamFullCalendarSerializer(serializers.ModelSerializer):
    streamer = StreamerSerializer(read_only=True)

    class Meta:
        model = ScheduledStream
        fields = ["pk", "streamer", "title", "start", "end", "category", "weekly"]

    def to_representation(self, instance: ScheduledStream):
        return {
            "id": instance.pk,
            "groupId": instance.streamer_id,
            "resourceId": instance.streamer_id,
            "start": instance.start,
            "end": instance.end,
            "title": instance.title,
            "url": instance.streamer.twitch_url,
            "extendedProps": ScheduledStreamSerializer(read_only=True).to_representation(instance),
        }


class StreamerResourceFullCalendarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Streamer
        fields = ["pk", "name"]

    def to_representation(self, instance):
        return {"id": instance.pk, "title": instance.name}


LiveAndScheduled = namedtuple("LiveAndScheduled", ("live", "scheduled"))


class LiveAndScheduledSerializer(serializers.Serializer):
    """
    API response to get all currently live and a few upcoming streams.
    """

    live = StreamerSerializer(many=True)
    scheduled = ScheduledStreamSerializer(many=True)

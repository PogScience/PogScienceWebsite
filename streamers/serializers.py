from rest_framework import serializers

from streamers.models import Streamer, ScheduledStream


class StreamerSerializer(serializers.ModelSerializer):
    colours_hsl = serializers.ListField()

    class Meta:
        model = Streamer
        fields = ["name", "twitch_login", "description", "profile_image", "colours_hsl", "live"]


class ScheduledStreamSerializer(serializers.ModelSerializer):
    streamer = StreamerSerializer(read_only=True)

    class Meta:
        model = ScheduledStream
        fields = ["pk", "streamer", "title", "start", "end", "category", "weekly"]


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

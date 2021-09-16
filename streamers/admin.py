from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import QuerySet
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from streamers.models import User, Streamer, ScheduledStream

admin.site.register(User, UserAdmin)


@admin.register(Streamer)
class StreamerAdmin(admin.ModelAdmin):
    list_display = ("name_with_image", "description", "live", "live_title")

    @admin.display(description="Name", ordering="twitch_login")
    def name_with_image(self, instance: Streamer):
        return format_html(
            """
            <div style="display: flex; flex-direction: row; align-items: center;">
                <figure style="margin: 4px"><img src="{}{}" alt="{}" style="border-radius: 31415926535px; width: 48px; height: 48px;" /></figure>
                <p style="flex: 4">{}<br /><span style="color: #ccc; font-weight: normal;">@{}</span></p>
            </div>
            """,
            settings.MEDIA_URL,
            instance.profile_image,
            instance.name,
            instance.name,
            instance.twitch_login,
        )


class FutureStreamFilter(admin.SimpleListFilter):
    title = _("date du stream")
    parameter_name = "when"

    def lookups(self, request, model_admin):
        return (
            ("future", _("Dans le futur")),
            ("live", _("Actuellement en live")),
            ("past", _("Dans le passé")),
        )

    def queryset(self, request, queryset: QuerySet):
        now = timezone.now()

        if self.value() == "future":
            return queryset.filter(start__gte=now)
        elif self.value() == "live":
            return queryset.filter(start__lte=now, end__gte=now)
        elif self.value() == "past":
            return queryset.filter(end__lte=now)


@admin.register(ScheduledStream)
class ScheduledStreamAdmin(admin.ModelAdmin):
    date_hierarchy = "start"
    list_display = ("title", "streamer_link", "category", "weekly", "start", "end", "duration")
    list_filter = (FutureStreamFilter, "streamer", "category", "weekly")
    list_select_related = ("streamer",)
    ordering = ("start",)
    search_fields = ("title", "streamer__name", "streamer__twitch_login", "category")
    readonly_fields = ("twitch_segment_id", "google_calendar_event_id")

    @admin.display(description=_("Streamer"), ordering="streamer__twitch_login")
    def streamer_link(self, instance):
        return format_html(
            '<a href="{}">{}</a>', f"https://twitch.tv/{instance.streamer.twitch_login}", instance.streamer.name
        )

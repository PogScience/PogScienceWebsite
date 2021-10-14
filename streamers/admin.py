from datetime import timedelta

from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.humanize.templatetags.humanize import NaturalTimeFormatter
from django.db.models import Q, QuerySet
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from streamers.models import EventSubSubscription, User, Streamer, ScheduledStream

admin.site.register(User, UserAdmin)
admin.site.register(EventSubSubscription)


class EventSubSubscriptionInline(admin.TabularInline):
    model = EventSubSubscription
    extra = 0
    fields = ("uuid", "type", "status", "last_seen")


@admin.register(Streamer)
class StreamerAdmin(admin.ModelAdmin):
    list_display = ("name_with_image", "description", "live", "live_title", "eventsub")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "twitch_login",
                    "twitch_id",
                    "profile_image",
                    "background_image",
                    "description",
                    "long_description",
                )
            },
        ),
        (
            _("État du live"),
            {
                "classes": ("collapse",),
                "description": _(
                    "Données sur le live en cours (s'il existe) du streamer. Ces données sont automatiquement mises à "
                    "jour."
                ),
                "fields": ("live", "live_title", "live_game_name", "live_started_at", "live_preview"),
            },
        ),
        (
            _("Que sont les abonnements EventSub ?"),
            {
                "description": _(
                    "<strong>EventSub est un outil de Twitch permettant d'être averti de tout changement sur l'état "
                    "des streams, ou d'autres informations, en temps réel.</strong> Pour chaque streamer, des "
                    "abonnements sont souscrits à Twitch pour que ce dernier nous informe lors qu'iel passe en live, "
                    "ou hors-ligne, ou change les informations de son stream, en temps réel. Si un de ces abonnements "
                    "n'est pas actif (car marqué comme tel ici), alors une tâche programmée automatique tentera de "
                    "renouveler l'abonnement sous une heure. Il est possible de passer ces éléments à « Non-souscrit » "
                    "manuellement pour forcer une re-souscription, mais tout ceci est normalement géré totalement "
                    "automatiquement."
                ),
                "fields": (),
            },
        ),
    )
    readonly_fields = ("twitch_id",)
    exclude = ("eventsub_subscriptions",)
    inlines = [EventSubSubscriptionInline]

    def get_queryset(self, request):
        """Prefetches eventsub subscriptions for list display"""
        queryset = super(StreamerAdmin, self).get_queryset(request)
        queryset = queryset.prefetch_related("eventsub_subscriptions")
        return queryset

    @admin.display(description="Name", ordering="twitch_login")
    def name_with_image(self, instance: Streamer):
        colours_boxes = ""
        for colour in instance.colours_hex:
            colours_boxes += format_html(
                '<span style="display: inline-block; width: .9em; height: .9em; border-radius: 2px; '
                'background-color: {}; margin: .4rem .2rem 0 0;"></span>',
                colour,
            )

        return format_html(
            """
            <div style="display: flex; flex-direction: row; align-items: center;">
                <figure style="margin: 4px"><img src="{}{}" alt="{}" style="border-radius: 31415926535px; width: 60px; height: 60px;" /></figure>
                <p style="flex: 4">{}<br /><span style="color: #ccc; font-weight: normal;">@{}</span><br/>{}</p>
            </div>
            """,
            settings.MEDIA_URL,
            instance.profile_image,
            instance.name,
            instance.name,
            instance.twitch_login,
            mark_safe(colours_boxes),
        )

    @admin.display(description="Abonnements EventSub")
    def eventsub(self, instance: Streamer):
        output = ""

        sub: EventSubSubscription
        for sub in instance.eventsub_subscriptions.all():
            if sub.status == EventSubSubscription.SUBSCRIBED:
                color = "70bf2b" if sub.last_seen_since < timedelta(days=40) else "ffcc00"
            elif sub.status == EventSubSubscription.UNSUBSCRIBED:
                color = "dd4646"
            elif sub.status == EventSubSubscription.PENDING:
                color = "4343f5"
            else:
                color = "ccc"

            output += format_html(
                """
                <div style="display: flex; flex-direction: row; align-items: center" title="{} – Dernière requête : {}">
                    <span style="display: inline-block;
                                 margin-right: .4em;
                                 width: .8em;
                                 height: .8em;
                                 border-radius: 314159265px;
                                 background-color: #{}"></span>
                    <code>{}</code>
                </div>
                """,
                sub.get_status_display(),
                NaturalTimeFormatter.string_for(sub.last_seen),
                color,
                sub.type,
            )
        return mark_safe(output)


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
            return queryset.filter(start__lte=now, end__gte=now, done=False)
        elif self.value() == "past":
            return queryset.filter(Q(end__lte=now) | Q(done=True))


@admin.register(ScheduledStream)
class ScheduledStreamAdmin(admin.ModelAdmin):
    date_hierarchy = "start"
    list_display = ("title", "streamer_link", "category", "weekly", "start", "end", "duration", "done")
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

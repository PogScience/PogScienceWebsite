import re
import string

import dateutil.parser as dp
import djclick as click
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from googleapiclient import discovery
from requests import HTTPError

from pogscience.twitch import get_twitch_client
from streamers.models import ScheduledStream, Streamer


@click.command()
@click.option(
    "--reset", default=False, is_flag=True, help="Deletes every existing scheduled stream before adding the new ones."
)
def command(reset):
    """
    Syncs the streams schedules from Twitch and Google Calendar.

    Loads the scheduled streams from Twitch and the configured Google Calendar,
    then merge the two sources and stores everything into the database. If
    already stored planned stream are re-imported, they are merged too, so this
    command can be called over and over again, e.g. in a cron job.
    """

    client = get_twitch_client()
    streamers = list(Streamer.objects.all())

    now = timezone.now()

    # To be able to associate Google Calendar events with streamers, we build a
    # list of alternate names for each streamer.
    streamers_alternate_names = {}
    re_split_by_caps = re.compile("[A-Z][^A-Z]*")

    # We remove those words from isolated detection worlds because they are too
    # broad.
    forbidden_solo_detection_words = [
        "Space",
        "Le",
        "Petit",
        "Professeur",
        "Hell",
        "Tout",
        "Se",
    ]
    forbidden_solo_detection_words.extend(string.ascii_lowercase)
    forbidden_solo_detection_words.extend(string.ascii_uppercase)

    for streamer in streamers:
        words_caps = re_split_by_caps.findall(streamer.name)
        words_underscores = streamer.name.split("_")
        alternate_names = [
            streamer.name,
            streamer.twitch_login,
            streamer.name.lower(),
            streamer.name.capitalize(),
            streamer.twitch_login.capitalize(),
        ]

        if words_caps:
            words_caps_filtered = [w for w in words_caps if w not in forbidden_solo_detection_words]
            alternate_names.extend(
                [
                    " ".join(words_caps),
                    "_".join(words_caps),
                    ".".join(words_caps),
                ]
            )
            alternate_names.extend(words_caps_filtered)

        if words_underscores:
            words_underscores_filtered = [w for w in words_underscores if w not in forbidden_solo_detection_words]
            alternate_names.extend(
                [
                    " ".join(words_underscores),
                    "_".join(words_underscores),
                    ".".join(words_underscores),
                ]
            )
            alternate_names.extend(words_underscores_filtered)

        alternate_names.extend([name.lower() for name in alternate_names])

        for name in alternate_names:
            streamers_alternate_names[name] = streamer

    # We first retrieve events from Twitch
    twitch_events = []
    with click.progressbar(
        streamers,
        label=click.style("Loading scheduled streams from Twitch...", fg="cyan", bold=True),
        item_show_func=lambda streamer: streamer.name if streamer is not None else None,
    ) as bar:
        for streamer in bar:
            try:
                schedule = client.get_schedule(streamer.twitch_id)
                for stream in schedule:
                    start = dp.parse(stream["start_time"])
                    if start - now >= settings.POG_SCHEDULE["FETCH_UNTIL"]:
                        break

                    twitch_events.append(
                        {
                            "streamer": streamer,
                            "title": stream["title"],
                            "start": start,
                            "end": dp.parse(stream["end_time"]),
                            "category": stream["category"]["name"],
                            "weekly": stream["is_recurring"],
                            "twitch_segment_id": stream["id"],
                            "google_calendar_event_id": None,
                        }
                    )

            except HTTPError:
                pass  # no schedule for this streamer, oh well.

    click.echo(f"  {len(twitch_events)} scheduled streams loaded from Twitch.")

    if settings.POG_SCHEDULE["GOOGLE_API_KEY"] and settings.POG_SCHEDULE["GOOGLE_CALENDAR_ID"]:

        # We then load Google Calendar events; we'll merge them with the former.
        click.secho("Loading scheduled streams from Google Calendar...", fg="cyan", bold=True, nl=False)
        gcal_service = discovery.build("calendar", "v3", developerKey=settings.POG_SCHEDULE["GOOGLE_API_KEY"])

        timeMin = now.isoformat()
        timeMax = (now + settings.POG_SCHEDULE["FETCH_UNTIL"]).isoformat()

        gcal_events_response = (
            gcal_service.events()
            .list(
                calendarId=settings.POG_SCHEDULE["GOOGLE_CALENDAR_ID"],
                singleEvents=True,
                orderBy="startTime",
                timeMin=timeMin,
                timeMax=timeMax,
                timeZone="UTC",
            )
            .execute()
        )

        gcal_raw_events = gcal_events_response.get("items", [])
        gcal_events = []
        gcal_errors = []

        # We try to associate events with streamers, matching channels names in the events
        # We first try to match the link in the event location, then at the beginning
        # of the summary, and if nothing is found, anywhere in the event summary.
        re_event_location_twitch_link = re.compile(r"https?://(www\.)?twitch\.tv/(?P<twitch_login>[a-zA-Z_]{4,25})")

        def has_streamer(streamer, lst):
            return any([streamer.name == entry["streamer"].name for entry in lst])

        def best_streamer(lst):
            return sorted(lst, key=lambda e: e["weight"], reverse=True)[0]["streamer"]

        for event in gcal_raw_events:
            start = dp.parse(event["start"].get("dateTime", event["start"].get("date")))
            end = dp.parse(event["end"].get("dateTime", event["end"].get("date")))

            if timezone.is_naive(start):
                start = timezone.make_aware(start)

            if timezone.is_naive(end):
                end = timezone.make_aware(end)

            event_streamers = []
            event_streamer_names_in_summary = []
            event_summary = event["summary"]

            if "location" in event:
                match = re_event_location_twitch_link.search(event["location"])
                if match:
                    streamer = streamers_alternate_names.get(match.group("twitch_login"))
                    event_streamers.append({"streamer": streamer, "weight": 100})
                    event_streamer_names_in_summary.extend([streamer.name, streamer.twitch_login])

            for name, streamer in streamers_alternate_names.items():
                if event["summary"].startswith(name):
                    if not has_streamer(streamer, event_streamers):
                        event_streamers.append({"streamer": streamer, "weight": 50})
                    event_streamer_names_in_summary.append(name)

            for name, streamer in streamers_alternate_names.items():
                if name in event["summary"]:
                    if not has_streamer(streamer, event_streamers):
                        event_streamers.append({"streamer": streamer, "weight": 10})
                    event_streamer_names_in_summary.append(name)
                    break

            if not event_streamers:
                gcal_errors.append(event["summary"])
                continue

            for name in event_streamer_names_in_summary:
                event_summary, n = re.subn(r"^" + re.escape(name) + r"\s{0,3}[/:–—-]", "", event_summary)
                if n > 0:
                    event_summary = event_summary.strip()
                    break

            gcal_events.append(
                {
                    "streamer": best_streamer(event_streamers),
                    "title": event_summary,
                    "start": start,
                    "end": end,
                    "category": None,
                    "weekly": "recurringEventId" in event,
                    "twitch_segment_id": None,
                    "google_calendar_event_id": event["id"],
                    "__potential_streamers": sorted(event_streamers, key=lambda e: e["weight"], reverse=True),
                }
            )

        click.secho(" OK ", fg="green", bold=True)
        click.echo(f"  {len(gcal_raw_events)} scheduled streams loaded from Google Calendar.")
        for error in gcal_errors:
            click.echo(f"  Unable to extract streamer from event “{error}”: ignored.", err=True)

        # For each Google Calendar event, we try to lookup for a Twitch event from
        # the same streamer (testing each potential one, the most likely first)
        # happening at the same time (times must overlap). If one is found, we merge
        # them, the Twitch event being the winner on conflicts.
        twitch_events_by_streamer = {}
        for event in twitch_events:
            twitch_events_by_streamer.setdefault(event["streamer"].twitch_login, [])
            twitch_events_by_streamer[event["streamer"].twitch_login].append(event)

        unique_gcal_events = []
        with click.progressbar(
            gcal_events,
            label=click.style("Merging Twitch and Google Calendar scheduled streams...", fg="cyan", bold=True),
        ) as bar:
            for gcal_event in bar:
                merged = False
                for ps in gcal_event["__potential_streamers"]:
                    potential_streamer, _ = ps.values()
                    merge_with = None
                    if potential_streamer.twitch_login not in twitch_events_by_streamer:
                        continue

                    for twitch_event in twitch_events_by_streamer[potential_streamer.twitch_login]:
                        if twitch_event["start"] <= gcal_event["end"] and twitch_event["end"] >= gcal_event["start"]:
                            merge_with = twitch_event
                            break

                    if merge_with:
                        merge_with["google_calendar_event_id"] = gcal_event["google_calendar_event_id"]
                        merged = True
                        break

                # If the event could not be merged with a Twitch event, it's a new one!
                # We'll add it to the Twitch events.
                if not merged:
                    del gcal_event["__potential_streamers"]
                    unique_gcal_events.append(gcal_event)

        twitch_events.extend(unique_gcal_events)

        click.echo(f"  {len(twitch_events)} scheduled streams loaded from both sources, after merge.")

    else:
        click.echo("No streams loaded from Google Calendar: API key or calendar ID not configured.")

    # Starting here, we'll start to store the new schedules into the database.
    # Hence, we start a transaction so the update is consistant.
    with transaction.atomic():
        if reset:
            click.secho("Removing existing scheduled streams...", fg="cyan", bold=True, nl=False)
            ScheduledStream.objects.filter(end__gte=now).delete()
            click.secho(" OK", fg="green", bold=True)

        click.secho("Fetching existing scheduled streams...", fg="cyan", bold=True, nl=False)

        stored_scheduled = ScheduledStream.objects.filter(end__gte=now)
        scheduled_by_source_id = {}
        for scheduled in stored_scheduled:
            scheduled_by_source_id[
                (scheduled.twitch_segment_id, scheduled.start, scheduled.streamer.twitch_id)
            ] = scheduled
            scheduled_by_source_id[
                (scheduled.google_calendar_event_id, scheduled.start, scheduled.streamer.twitch_id)
            ] = scheduled

        click.secho(" OK", fg="green", bold=True)

        def has_stored_schedule(schedule):
            return (
                schedule["twitch_segment_id"],
                schedule["start"],
                schedule["streamer"].twitch_id,
            ) in scheduled_by_source_id or (
                schedule["google_calendar_event_id"],
                schedule["start"],
                schedule["streamer"].twitch_id,
            ) in scheduled_by_source_id

        def get_stored_schedule(schedule):
            return scheduled_by_source_id.get(
                (schedule["twitch_segment_id"], schedule["start"], schedule["streamer"].twitch_id),
                scheduled_by_source_id.get(
                    (schedule["google_calendar_event_id"], schedule["start"], schedule["streamer"].twitch_id)
                ),
            )

        scheduled_to_update = []

        with click.progressbar(
            twitch_events, label=click.style("Saving scheduled streams to database...", fg="cyan", bold=True)
        ) as bar:
            for event in bar:
                # The scheduled stream already exist in the database
                if has_stored_schedule(event):
                    scheduled: ScheduledStream = get_stored_schedule(event)

                    # Update the record with the data collected, to allow for updates if needed
                    if scheduled is not None:
                        scheduled.streamer = event["streamer"]
                        scheduled.title = event["title"]
                        scheduled.start = event["start"]
                        scheduled.end = event["end"]
                        scheduled.category = event["category"]
                        scheduled.weekly = event["weekly"]
                        scheduled.twitch_segment_id = event["twitch_segment_id"]
                        scheduled.google_calendar_event_id = event["google_calendar_event_id"]

                        scheduled_to_update.append(scheduled)
                        continue

                # The scheduled stream is new
                ScheduledStream(
                    streamer=event["streamer"],
                    title=event["title"],
                    start=event["start"],
                    end=event["end"],
                    category=event["category"],
                    weekly=event["weekly"],
                    twitch_segment_id=event["twitch_segment_id"],
                    google_calendar_event_id=event["google_calendar_event_id"],
                ).save()

        click.secho("Updating existing scheduled streams...", fg="cyan", bold=True, nl=False)
        ScheduledStream.objects.bulk_update(
            scheduled_to_update,
            fields=[
                "streamer",
                "title",
                "start",
                "end",
                "category",
                "weekly",
                "twitch_segment_id",
                "google_calendar_event_id",
            ],
        )

        click.secho(" OK", fg="green", bold=True)

        # We delete streams in the future that were not collected by the script,
        # but are stored in the database: these streams existed before but are now
        # deleted, so we delete them in our database too.
        click.secho("Deleting removed scheduled streams...", fg="cyan", bold=True, nl=False)
        twitch_segments_ids = [s["twitch_segment_id"] for s in twitch_events]
        google_calendar_event_ids = [s["google_calendar_event_id"] for s in twitch_events]
        deleted, _ = (
            ScheduledStream.objects.filter(end__gte=now)
            .filter(
                ~Q(twitch_segment_id__in=twitch_segments_ids)
                & ~Q(google_calendar_event_id__in=google_calendar_event_ids)
            )
            .delete()
        )
        click.secho(" OK ", fg="green", bold=True)
        click.echo(f"  {deleted} removed scheduled streams deleted.")

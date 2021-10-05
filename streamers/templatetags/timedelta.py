from datetime import timedelta

from django import template
from django.utils.translation import gettext, ngettext


register = template.Library()


@register.filter
def timedelta_short(delta: timedelta) -> str:
    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, _ = divmod(remainder, 60)

    if days > 0:
        return ngettext(
            "%(days)d jour, %(hours)02dh%(minutes)02d", "%(days)d jours, %(hours)02dh%(minutes)02d", days
        ) % {
            "days": days,
            "hours": hours,
            "minutes": minutes,
        }
    else:
        return gettext("%(hours)02dh%(minutes)02d") % {"hours": hours, "minutes": minutes}

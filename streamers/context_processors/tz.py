def tz(request):
    from django.utils import timezone

    tz_name = timezone.get_current_timezone_name()

    return {"TIME_ZONE": tz_name, "TIME_ZONE_CITY": tz_name.split("/")[-1]}

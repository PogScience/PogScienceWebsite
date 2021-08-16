from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from streamers.models import User, Streamer

admin.site.register(User, UserAdmin)
admin.site.register(Streamer)

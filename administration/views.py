import re

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.forms import model_to_dict
from django.http import Http404, JsonResponse
from django.urls import reverse_lazy
from django.views.generic import FormView, ListView, RedirectView

from pogscience.twitch import get_twitch_client

from administration.forms import AddStreamersForm
from streamers.models import Streamer


class IndexView(LoginRequiredMixin, RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.has_perm("streamers.view_streamer"):
            return reverse_lazy("administration:streamers")

        raise Http404()


class StreamersView(PermissionRequiredMixin, LoginRequiredMixin, ListView):
    permission_required = ["streamers.view_streamer"]
    model = Streamer
    context_object_name = "streamers"
    template_name = "streamers/list.html"

    extra_context = {
        'add_streamers_form': AddStreamersForm()
    }


class AddStreamersView(PermissionRequiredMixin, LoginRequiredMixin, FormView):
    permission_required = ["streamers.add_streamer"]
    template_name = "streamers/add.html"
    form_class = AddStreamersForm
    success_url = reverse_lazy("administration:streamers")

    def form_valid(self, form):
        # Splits the names at whitespaces (including new lines) and filter out
        # empty strings left for multiple separators.
        streamer_names = [name for name in re.split(r',|\s', form.cleaned_data['streamers_names'].strip()) if name]

        streamers_twitch = get_twitch_client().get_users(streamer_names)
        streamers = []

        with transaction.atomic():
            for streamer in streamers_twitch:
                try:
                    streamer_model: Streamer = Streamer.objects.get(twitch_login=streamer['login'])
                except Streamer.DoesNotExist:
                    streamer_model: Streamer = Streamer()

                streamer_model.update_from_twitch_data(streamer)
                streamer_model.save()

                streamer_dict = model_to_dict(streamer_model)
                streamer_dict['profile_image'] = streamer_model.profile_image.url

                streamers.append(streamer_dict)

        return JsonResponse({
            'streamers': streamers
        })

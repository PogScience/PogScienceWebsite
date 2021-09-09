import re
from http import HTTPStatus

from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.forms import model_to_dict
from django.http import Http404, HttpResponse, JsonResponse
from django.urls import reverse_lazy
from django.views import View
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
    partial = False
    permission_required = ["streamers.view_streamer"]
    model = Streamer
    context_object_name = "streamers"

    extra_context = {
        'add_streamers_form': AddStreamersForm()
    }

    def get_template_names(self):
        return "streamers/list.partial.html" if self.partial else "streamers/list.html"


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

        with transaction.atomic():
            for streamer in streamers_twitch:
                try:
                    streamer_model: Streamer = Streamer.objects.get(twitch_login=streamer['login'])
                except Streamer.DoesNotExist:
                    streamer_model: Streamer = Streamer()

                streamer_model.update_from_twitch_data(streamer)
                streamer_model.save()

        return HttpResponse(status=HTTPStatus.CREATED)


class UpdateStreamersFromTwitch(PermissionRequiredMixin, LoginRequiredMixin, View):
    permission_required = ["streamers.change_streamer"]

    def post(self, request):
        streamers = Streamer.objects.all()
        ids = [streamer.twitch_id for streamer in streamers]
        # We use string keys because Twitch returns string ids
        streamers = {str(streamer.twitch_id): streamer for streamer in streamers}

        streamers_twitch = get_twitch_client().get_users(ids=ids)

        for streamer in streamers_twitch:
            streamer_model = streamers[streamer['id']]
            streamer_model.update_from_twitch_data(streamer)
            streamer_model.save()

        return HttpResponse(status=HTTPStatus.NO_CONTENT)

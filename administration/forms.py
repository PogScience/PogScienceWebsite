from django import forms
from django.utils.translation import gettext_lazy as _


class AddStreamersForm(forms.Form):
    streamers_names = forms.CharField(
        label=_("Streamers à ajouter"),
        help_text=_(
            "Entrez la liste des pseudos Twitch des streamers à ajouter, en "
            "les séparant par des virgules ou des sauts de ligne."
        ),
        max_length=100,
        widget=forms.Textarea,
    )

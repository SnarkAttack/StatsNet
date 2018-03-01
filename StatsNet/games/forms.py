from django import forms
from .models import Identity

def get_runner_ids():
    runner_ids = [(identity.code, identity.title) for identity in Identity.objects.filter(side_code='runner').order_by('title')]
    runner_ids.insert(0, (None, '---'))
    return runner_ids

def get_corp_ids():
    corp_ids = [(identity.code, identity.title) for identity in Identity.objects.filter(side_code='corp').order_by('title')]
    corp_ids.insert(0, (None, '---'))
    return corp_ids

class GameLogForm(forms.Form):
    player_side = forms.ChoiceField(choices=[(True, 'Runner'), (False, 'Corp')])
    runner_id = forms.ChoiceField(choices=get_runner_ids())
    runner_score = forms.IntegerField()
    corp_id = forms.ChoiceField(choices=get_corp_ids())
    corp_score = forms.IntegerField()
    winner = forms.ChoiceField(choices=[(True, 'Runner'), (False, 'Corp')])
    win_type = forms.ChoiceField(choices=[(0, 'Agenda Points'), (1, 'Flatline'), (2, 'Mill'), (3, 'Concede')])
    # Just want to fill in for based on time entered
    opponent_username = forms.CharField(required=False)

class StatsRequestForm(forms.Form):
    player_side = forms.ChoiceField(choices=[(True, 'Runner'), (False, 'Corp')])
    runner_faction = forms.ChoiceField(choices=[(None, '---'), ('anarch', 'Anarch'), ('criminal', 'Criminal'), ('shaper', 'Shaper'), ('sunny-lebeau', 'Sunny'), ('adam', 'Adam'), ('apex', 'Apex')], required=False)
    runner_id = forms.ChoiceField(choices=get_runner_ids(), required=False)
    corp_faction = forms.ChoiceField(choices=[(None, '---'), ('haas-bioroid', 'Haas-Bioroid'), ('jinteki', 'Jinteki'), ('nbn', 'NBN'), ('weyland-consortium', 'Weyland')], required=False)
    corp_id = forms.ChoiceField(choices=get_corp_ids(), required=False)

class GameLogJintekiTextForm(forms.Form):
    full_text = forms.CharField(widget=forms.Textarea)
    full_detail = forms.BooleanField(required=False)
    runner_id = forms.ChoiceField(choices=get_runner_ids())
    corp_id = forms.ChoiceField(choices=get_corp_ids())
    deck_name = forms.CharField(required=False)

class RegisterUsernameForm(forms.Form):
    new_username = forms.CharField(max_length=32)

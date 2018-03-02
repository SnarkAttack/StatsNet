from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.views import View
from django.urls import reverse
from django.utils import timezone
import urllib2
import json
import datetime
import pytz
from tzlocal import get_localzone

from ..models import Game, Identity, JintekiUsername
from ..forms import GameLogForm, StatsRequestForm, GameLogJintekiTextForm, RegisterUsernameForm
from .views import GameListDisplay, compile_game_detail_list

class BaseStats():

    def __init__(self, opp_id_num, opp_side, num_wins, num_losses):
        if(opp_side):
            opp_name = Identity.objects.filter(code=opp_id_num)[0].title.split(':')[0]
        else:
            corp_start = Identity.objects.filter(code=opp_id_num)[0].title.split(':')
            if(corp_start[0] == 'Haas-Bioroid' or corp_start[0] == 'Jinteki' or
                corp_start[0] == 'NBN' or corp_start[0] == 'Weyland Consortium'):
                opp_name = corp_start[1].strip()
            else:
                opp_name = corp_start[0].strip()
        self.opp_name = opp_name
        self.num_wins = num_wins
        self.num_losses = num_losses
        if num_losses == 0:
            self.winrate = '100.0'
        else:
            self.winrate = str(round(float(num_wins)/(num_losses+num_wins) * 100, 1));

class StatsViewer(View):

    def get(self, request):
        username = request.user.username
        data = request.GET
        stats_request_form = StatsRequestForm()
        player_is_runner = True
        if(data):
            games = None

            if(data.get('player_side') == 'True'):
                games = Game.objects.filter(runner_name=username)
            else:
                player_is_runner = False
                games = Game.objects.filter(corp_name=username)

            if(data.get('runner_id')):
                games = games.filter(runner_id=data['runner_id'])

            if(data.get('corp_id')):
                games = games.filter(corp_id=data['corp_id'])

            if(data.get('runner_faction')):
                games = games.filter(runner_id__in=get_runner_faction_ids(data['runner_faction']))

            if(data.get('corp_id')):
                games = games.filter(corp_id__in=get_corp_faction_ids(data['corp_faction']))

            base_stats = {}
            totals = {'win': 0, 'loss': 0}
            for game in games:
                if(player_is_runner):
                    id = game.runner_id
                else:
                    id = game.corp_id
                base_stats[id] = base_stats.get(id, {'win': 0, 'loss': 0})
                if game.winner == player_is_runner:
                    totals['win'] += 1
                    base_stats[id]['win'] += 1
                else:
                    totals['loss'] += 1
                    base_stats[id]['loss'] += 1
            opp_list = []
            for opp in base_stats:
                opp_list.append(BaseStats(opp, False, base_stats[opp]['win'], base_stats[opp]['loss']))
            if totals['win'] != 0 or totals['loss'] != 0:
                totals['winrate'] = str(round(float(totals['win'])/(totals['win']+totals['loss']) * 100, 1));
            context = {'stats_request_form': stats_request_form, 'games': compile_game_detail_list(games, username), 'stats': sorted(opp_list, key=lambda game: game.opp_name), 'totals': totals}
            return render(request, 'games/request_stats.html', context)


def get_runner_faction_ids(faction):
    runner_faction_ids = [identity.code for identity in Identity.objects.filter(side_code='runner', faction_code=faction)]
    return runner_faction_ids

def get_corp_faction_ids(faction):
    corp_faction_ids = [identity.code for identity in Identity.objects.filter(side_code='corp', faction_code=faction)]
    return corp_faction_ids

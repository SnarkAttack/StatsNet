from django.shortcuts import get_object_or_404, render
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
from ..forms import GameLogForm, StatsRequestForm, GameLogJintekiTextForm, RegisterUsernameForm

from games.models import Game, Identity
from games.forms import GameLogForm, StatsRequestForm, GameLogJintekiTextForm

username = 'SnarkAttack'

def index(request):
    return HttpResponse("Hello, world. You're at the games index.")

def record_game(request):
    # get_ids()
    game_log_form = GameLogForm()
    game_log_jinteki_text_form = GameLogJintekiTextForm()
    context = {'game_log_form': game_log_form, 'game_log_jinteki_text_form': game_log_jinteki_text_form}
    return render(request, 'games/record_game.html', context)

def get_game(game):
    runner = get_object_or_404(Identity, code=game.runner_id)
    corp = get_object_or_404(Identity, code=game.corp_id)

    endgame_string = ""

    local_tz = get_localzone()
    timezone.activate(local_tz)
    if game.winner == game.player_side:
        if game.win_type == 0:
            endgame_string = 'Won on agendas'
        elif game.win_type == 1:
            endgame_string = 'Won by flatrunning the runner'
        elif game.win_type == 2:
            endgame_string == 'Won by milling the corp'
        elif game.win_type == 3:
            endgame_string = 'Won because our opponent folded like a house of cards'
    else:
        if game.win_type == 0:
            endgame_string = 'Lost on agendas'
        elif game.win_type == 1:
            endgame_string = 'Lost by getting murdered'
        elif game.win_type == 2:
            endgame_string == 'Lost by getting milled'
        elif game.win_type == 3:
            endgame_string = 'Never forgive yourself'

    return {'game': game, 'runner_name': runner.title, 'corp_name': corp.title, 'endgame_text': endgame_string}

def view_game(request, game_id):
    game = get_object_or_404(Game, pk=game_id)
    return render(request, 'games/game_details.html', get_game(game))

class GameListDisplay():

    def __init__(self, player_id_name, opp_id_name, player_score, opp_score, game_id, result_text):
        self.player_name = player_id_name
        self.opp_name = opp_id_name
        self.player_score = player_score
        self.opp_score = opp_score
        self.id = game_id
        self.result_text = result_text

def compile_game_detail_list(games_list, username):
    game_details_list = []
    for game in games_list:
        runner_name = Identity.objects.filter(code=game.runner_id)[0].title.split(':')[0]
        corp_start = Identity.objects.filter(code=game.corp_id)[0].title.split(':')
        if(corp_start[0] == 'Haas-Bioroid' or corp_start[0] == 'Jinteki' or
            corp_start[0] == 'NBN' or corp_start[0] == 'Weyland Consortium'):
            corp_name = corp_start[1].strip()
        else:
            corp_name = corp_start[0].strip()

        if(game.player_side):
            player_name = runner_name
            opp_name = corp_name
            player_score = game.runner_score
            opp_score = game.corp_score
        else:
            player_name = corp_name
            opp_name = runner_name
            player_score = game.corp_score
            opp_score = game.runner_score

        if game.winner == game.player_side:
            result_text = "Win"
        else:
            result_text = "Loss"

        game_detail = GameListDisplay(player_name, opp_name, player_score, opp_score, game.id, result_text)

        game_details_list.append(game_detail)

    return game_details_list

def list_games(request):
    latest_games_list = Game.objects.order_by('-game_date')[:10]
    context = {
        'game_details_list': compile_game_detail_list(latest_games_list),
    }
    return render(request, 'games/list_games.html', context)

def get_ids(request):
    card_data = urllib2.urlopen("https://netrunnerdb.com/api/2.0/public/cards").read()
    json_cards = json.loads(card_data)
    all_id_data = [card for card in json_cards['data'] if card['type_code'] == 'identity']
    for id_data in all_id_data:
        (identity, created) = Identity.objects.register_id(id_data['code'], id_data['title'], id_data['faction_code'], id_data['side_code'])
        if created:
            identity.save()
    next = request.POST.get('next', '/')
    return HttpResponseRedirect(next)

class GameListDisplay():

    def __init__(self, player_id_name, opp_id_name, player_score, opp_score, game_id, result_text):
        self.player_name = player_id_name
        self.opp_name = opp_id_name
        self.player_score = player_score
        self.opp_score = opp_score
        self.id = game_id
        self.result_text = result_text

def compile_game_detail_list(games_list, username):
    game_details_list = []
    for game in games_list:
        runner_name = Identity.objects.filter(code=game.runner_id)[0].title.split(':')[0]
        corp_start = Identity.objects.filter(code=game.corp_id)[0].title.split(':')
        player_side = True
        if(corp_start[0] == 'Haas-Bioroid' or corp_start[0] == 'Jinteki' or
            corp_start[0] == 'NBN' or corp_start[0] == 'Weyland Consortium'):
            corp_name = corp_start[1].strip()
        else:
            corp_name = corp_start[0].strip()

        if(game.runner_name == username):
            player_side = True
            player_name = runner_name
            opp_name = corp_name
            player_score = game.runner_score
            opp_score = game.corp_score
        elif(game.corp_name == username):
            player_side = False
            player_name = corp_name
            opp_name = runner_name
            player_score = game.corp_score
            opp_score = game.runner_score

        if game.winner == player_side:
            result_text = "Win"
        else:
            result_text = "Loss"

        game_detail = GameListDisplay(player_name, opp_name, player_score, opp_score, game.id, result_text)

        game_details_list.append(game_detail)

    return game_details_list

@login_required(login_url=settings.LOGIN_URL)
def list_games(request):
    latest_games_list = Game.objects.order_by('-game_date')[:10]
    if request.user.is_authenticated():
        context = {
            'game_details_list': compile_game_detail_list(latest_games_list, request.user.username),
        }
        return render(request, 'games/list_games.html', context)
    else:
        return None

def get_ids(request):
    card_data = urllib2.urlopen("https://netrunnerdb.com/api/2.0/public/cards").read()
    json_cards = json.loads(card_data)
    all_id_data = [card for card in json_cards['data'] if card['type_code'] == 'identity']
    for id_data in all_id_data:
        (identity, created) = Identity.objects.register_id(id_data['code'], id_data['title'], id_data['faction_code'], id_data['side_code'])
        if created:
            identity.save()
    next = request.POST.get('next', '/')
    return HttpResponseRedirect(next)


@login_required(login_url=settings.LOGIN_URL)
def usernames(request):
    register_username_form = RegisterUsernameForm()
    context = {'register_username_form': register_username_form}
    return render(request, 'games/register_username.html', context)

@login_required(login_url=settings.LOGIN_URL)
def register_username(request):
    data = request.POST
    new_username = data['new_username']
    JintekiUsername.objects.register_username(new_username, request.user.username)
    return render(request, '/games/')

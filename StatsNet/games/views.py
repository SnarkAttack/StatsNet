from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseRedirect
from django.views import View
from django.urls import reverse
from django.utils import timezone
import urllib2
import json
import datetime
import pytz
from tzlocal import get_localzone

from .models import Game, Identity
from .forms import GameLogForm, StatsRequestForm, GameLogJintekiTextForm

username = 'SnarkAttack'

def index(request):
    return HttpResponse("Hello, world. You're at the games index.")

def record_game(request):
    # get_ids()
    game_log_form = GameLogForm()
    game_log_jinteki_text_form = GameLogJintekiTextForm()
    context = {'game_log_form': game_log_form, 'game_log_jinteki_text_form': game_log_jinteki_text_form}
    return render(request, 'games/record_game.html', context)

class GameLogger(View):

    def post(self, request):
        data = request.POST
        winner = True if data['winner'] == 'True' else False
        player_side = True if data['player_side'] == 'True' else False
        online = True if data.get('online') == 'on' else False

        (game, created) = Game.objects.store_game(
                win_type=int(data['win_type']),
                winner=winner,
                corp_id=int(data['corp_id']),
                player_side=player_side,
                corp_score=int(data['corp_score']),
                runner_id=int(data['runner_id']),
                runner_score=int(data['runner_score']),
                game_date=datetime.datetime.now(),
                opponent_username=data['opponent_username'],
                #online=online,
                exact_match=1
        )
        if created:
            game.save()
            return HttpResponseRedirect(reverse("games:list_games"))
        else:
            (retry_game, retry_created) = Game.objects.store_game(
                    win_type=int(data['win_type']),
                    winner=winner,
                    corp_id=int(data['corp_id']),
                    player_side=player_side,
                    corp_score=int(data['corp_score']),
                    runner_id=int(data['runner_id']),
                    runner_score=int(data['runner_score']),
                    game_date=datetime.datetime.now(),
                    opponent_username=data['opponent_username'],
                    #online=online,
                    exact_match=game.exact_match+1
            )
            if retry_created:
                game.save()
                return HttpResponseRedirect(reverse("games:list_games"))
            else:
                return HttpResponseRedirect(reverse("games:list_games"))

def get_game(game):
    runner = get_object_or_404(Identity, code=game.runner_id)
    corp = get_object_or_404(Identity, code=game.corp_id)

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
        global username
        data = request.GET
        stats_request_form = StatsRequestForm()
        if(data):
            games = None
            if data.get('runner_name') != username:
                # We are looking at runner stats
                if data.get('runner_id'):
                    if data.get('corp_id'):
                        games = Game.objects.filter(player_side=True, runner_id__in=[data['runner_id']], corp_id__in=[data['corp_id']])
                    elif data.get('corp_faction'):
                        games = Game.objects.filter(player_side=True, runner_id__in=[data['runner_id']], corp_id__in=get_corp_faction_ids(data['corp_faction']))
                    else:
                        games = Game.objects.filter(player_side=True, runner_id__in=[data['runner_id']])
                elif data.get('runner_faction'):
                    if data.get('corp_id'):
                        games = Game.objects.filter(player_side=True, runner_id__in=get_runner_faction_ids(data['runner_faction']), corp_id__in=[data['corp_id']])
                    elif data.get('corp_faction'):
                        games = Game.objects.filter(player_side=True, runner_id__in=get_runner_faction_ids(data['runner_faction']), corp_id__in=get_corp_faction_ids(data['corp_faction']))
                    else:
                        games = Game.objects.filter(player_side=True, runner_id__in=get_runner_faction_ids(data['runner_faction']))
                else:
                    if data.get('corp_id'):
                        games = Game.objects.filter(player_side=True, corp_id__in=[data['corp_id']])
                    elif data.get('corp_faction'):
                        games = Game.objects.filter(player_side=True, corp_id__in=get_corp_faction_ids(data['corp_faction']))
                    else:
                        games = Game.objects.filter(player_side=True)

                base_stats = {}
                totals = {'win': 0, 'loss': 0}
                for game in games:
                    base_stats[game.corp_id] = base_stats.get(game.corp_id, {'win': 0, 'loss': 0})
                    if game.winner:
                        totals['win'] += 1
                        base_stats[game.corp_id]['win'] += 1
                    else:
                        totals['loss'] += 1
                        base_stats[game.corp_id]['loss'] += 1
                opp_list = []
                for opp in base_stats:
                    opp_list.append(BaseStats(opp, False, base_stats[opp]['win'], base_stats[opp]['loss']))
                if totals['win'] != 0 or totals['loss'] != 0:
                    totals['winrate'] = str(round(float(totals['win'])/(totals['win']+totals['loss']) * 100, 1));
                context = {'stats_request_form': stats_request_form, 'games': compile_game_detail_list(games), 'stats': sorted(opp_list, key=lambda game: game.opp_name), 'totals': totals}
                return render(request, 'games/request_stats.html', context)

            else:
                if data.get('corp_id'):
                    if data.get('runner_id'):
                        games = Game.objects.filter(player_side=False, corp_id__in=[data['corp_id']], runner_id__in=[data['runner_id']])
                    elif data.get('runner_faction'):
                        games = Game.objects.filter(player_side=False, corp_id__in=[data['corp_id']], runner_id__in=get_corp_faction_ids(data['runner_faction']))
                    else:
                        games = Game.objects.filter(player_side=False, corp_id__in=[data['corp_id']])
                elif data.get('corp_faction'):
                    if data.get('runner_id'):
                        games = Game.objects.filter(player_side=False, corp_id__in=get_corp_faction_ids(data['corp_faction']), runner_id__in=[data['runner_id']])
                    elif data.get('runner_faction'):
                        games = Game.objects.filter(player_side=False, corp_id__in=get_corp_faction_ids(data['corp_faction']), runner_id__in=get_corp_faction_ids(data['runner_faction']))
                    else:
                        games = Game.objects.filter(player_side=False, corp_id__in=get_corp_faction_ids(data['corp_faction']))
                else:
                    if data.get('runner_id'):
                        games = Game.objects.filter(player_side=False, runner_id__in=[data['runner_id']])
                    elif data.get('runner_faction'):
                        games = Game.objects.filter(player_side=False, runner_id__in=get_runner_faction_ids(data['runner_faction']))
                    else:
                        games = Game.objects.filter(player_side=False)

                base_stats = {}
                totals = {'win': 0, 'loss': 0}
                for game in games:
                    base_stats[game.runner_id] = base_stats.get(game.runner_id, {'win': 0, 'loss': 0})
                    if not game.winner:
                        totals['win'] += 1
                        base_stats[game.runner_id]['win'] += 1
                    else:
                        totals['loss'] += 1
                        base_stats[game.runner_id]['loss'] += 1
                opp_list = []
                for opp in base_stats:
                    opp_list.append(BaseStats(opp, False, base_stats[opp]['win'], base_stats[opp]['loss']))
                if totals['win'] != 0 or totals['loss'] != 0:
                    totals['winrate'] = str(round(float(totals['win'])/(totals['win']+totals['loss']) * 100, 1));
                context = {'stats_request_form': stats_request_form, 'games': compile_game_detail_list(games), 'stats': sorted(opp_list, key=lambda game: game.opp_name), 'totals': totals}
                return render(request, 'games/request_stats.html', context)
        else:
            context = {'stats_request_form': stats_request_form}
            return render(request, 'games/request_stats.html', context)

def get_runner_faction_ids(faction):
    runner_faction_ids = [identity.code for identity in Identity.objects.filter(side_code='runner', faction_code=faction)]
    return runner_faction_ids

def get_corp_faction_ids(faction):
    corp_faction_ids = [identity.code for identity in Identity.objects.filter(side_code='corp', faction_code=faction)]
    return corp_faction_ids

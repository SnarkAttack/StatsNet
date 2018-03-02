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
import re
import hashlib

from ..models import Game
from ..forms import GameLogForm, GameLogJintekiTextForm

class GameLogger(View):

    def post(self, request):
        data = request.POST
        winner = True if data['winner'] == 'True' else False
        runner_name = request.user.username if data['player_side'] == 'True' else data['opponent_username']
        corp_name = data['opponent_username'] if data['player_side'] == 'True' else request.user.username

        fulltext = fulltext.strip()
        encoded_full = fulltext.encode('utf-8')
        game_hash = hashlib.sha256(encoded_full).hexdigest()

        (game, created) = Game.objects.store_game(
                win_type=int(data['win_type']),
                winner=winner,
                corp_id=int(data['corp_id']),
                runner_name=runner_name,
                corp_score=int(data['corp_score']),
                runner_id=int(data['runner_id']),
                runner_score=int(data['runner_score']),
                game_date=datetime.datetime.now(),
                corp_name=corp_name,
                #online=online,
                game_hash=game_hash,
        )
        if created:
            game.save()
            return HttpResponseRedirect(reverse("games:list_games"))
        else:
            print "Game not added"
            return HttpResponseRedirect(reverse("games:list_games"))

@login_required(login_url=settings.LOGIN_URL)
def record_game(request):
    # get_ids()
    game_log_form = GameLogForm()
    game_log_jinteki_text_form = GameLogJintekiTextForm()
    context = {'game_log_form': game_log_form, 'game_log_jinteki_text_form': game_log_jinteki_text_form}
    return render(request, 'games/record_game.html', context)

class GameLoggerFullText(View):

    def post(self, request):
        data = request.POST
        stats = gather_stats(data['full_text'])

        hash_list = Game.objects.values_list('game_hash', flat=True)
        exists = False
        for game_hash in hash_list:
            if game_hash == stats['hash']:
                exists = True
                break

        if not exists:
            (game, created) = Game.objects.store_game(
                    win_type=int(stats['win_type']),
                    winner=stats['winner'],
                    corp_id=int(data['corp_id']),
                    runner_name=stats['runner_name'],
                    corp_score=int(stats['corp_score']),
                    runner_id=int(data['runner_id']),
                    runner_score=int(stats['runner_score']),
                    game_date=datetime.datetime.now(),
                    corp_name=stats['corp_name'],
                    runner_credits = stats['runner_click_for_credit'],
                    corp_credits = stats['corp_click_for_credit'],
                    runner_draws = stats['runner_draws'],
                    corp_draws = stats['corp_draws'],
                    runner_installs = stats['installed_run'],
                    corp_installs = stats['installed_corp'],
                    runner_mulligan = stats['runner_mulligan'],
                    corp_mulligan = stats['corp_mulligan'],
                    runs = stats['runs'],
                    turns = stats['turns'],
                    deck_name = data['deck_name'],
                    #online=online,
                    game_hash = stats['hash'],
            )
            if created:
                game.save()
                return HttpResponseRedirect(reverse("games:list_games"))
            else:
                print "Could not make game"
                return HttpResponseRedirect(reverse("games:list_games"))
        else:
            print "Game already recorded"
            return HttpResponseRedirect(reverse("games:list_games"))


def scoring_action(line):
    if "scores" in line or "steals" in line or ("as an agenda" in line and "force" not in line) or ("to add it to their score area" in line):
        return True
    else:
        return False

def gather_stats(game_log):

    stats = {'corp_name': "", 'runner_name': "", 'runner_click_for_credit': 0,
                'runner_draws': 0, 'runner_played': {}, 'corp_played': {}, 'installed_run': 0,
                'installed_corp': 0, 'corp_click_for_credit': 0, 'corp_uses': {}, 'corp_draws': 0,
                'runner_score': 0, 'corp_score': 0, 'runner_agendas': {},
                'corp_agendas': {}, 'runner_uses': {}, 'pumps': {}, 'endTurn': {},
                'runs': 0, "ICE": {}, 'server': {}, 'rez': {}, 'advanceCount': 0, 'winner': None,
                "turns": 0, 'win_type': -1, 'runner_mullgan': True, 'corp_mulligan': True, 'hash': ""}

    game_text = []
    for line in game_log.split('\n'):
        game_text.append(line.rstrip())
        if "wins the game" in line:
            break

        (runner_name, corp_name, runner_mulligan, corp_mulligan) = getPlayers(game_text)

    return getStats(game_text, runner_name, corp_name, runner_mulligan, corp_mulligan, stats)

def getPlayers(game_text):
    corp_name = ""
    runner_name = ""
    corp_mulligan = False
    runner_mulligan = False
    for line in game_text:
        if 'takes a mulligan.' in line:
            if corp_name is "":
                corp_name = line[:-len(' takes a mulligan.')]
                corp_mulligan = True
            else:
                runner_name = line[:-len(' takes a mulligan.')]
                runner_mulligan = True
                break
        elif 'keeps their hand.' in line:
            if corp_name is "":
                corp_name = line[:-len(' keeps their hand.')]
            else:
                runner_name = line[:-len(' keeps their hand.')]
                break

    return (runner_name, corp_name, runner_mulligan, corp_mulligan)

def getStats(game_text, runner_name, corp_name, runner_mulligan, corp_mulligan, stats):
    stats['runner_name'] = runner_name
    stats['corp_name'] = corp_name
    stats['runner_mulligan'] = runner_mulligan
    stats['corp_mulligan'] = corp_mulligan
    fulltext = ""
    for line in game_text:
        if line.startswith("!"):
            continue
        if "spends  to gain 1 ." in line:
            if runner_name in line:
                stats['runner_click_for_credit'] = stats.get('runner_click_for_credit', 0) + 1
            else:
                stats['corp_click_for_credit'] = stats.get('corp_click_for_credit', 0) + 1
        elif " spends  to draw " in line:
            if runner_name in line:
                stats['runner_draws'] = stats.get('runner_draws', 0) + 1
            else:
                stats['corp_draws'] = stats.get('corp_draws', 0) + 1
        elif "to install a card in" in line:
            stats['installed_corp'] = stats.get('installed_corp', 0) + 1
        elif "to install ICE protecting" in line:
            stats['installed_corp'] = stats.get('installed_corp', 0) + 1
        elif "to install " in line and "uses" not in line:
            stats['installed_run'] = stats.get('installed_run', 0) + 1
        elif "started their turn" in line:
            run_count = re.search(r'started their turn ([\d]+)', line, re.UNICODE)
            stats['turns'] = int(run_count.group(1))
        elif "to make a run" in line:
            stats['runs'] = stats.get('runs', 0) + 1
        elif scoring_action(line):
            if runner_name in line:
                point_value = re.search(r' (scores|steals) ([&"\'!:\w\s-]+) and gains ([\d]+) agenda point', line, re.UNICODE)
                if point_value is None:
                    point_value = re.search(r'(adds) ([&"\'!:\w\s-]+) to their score area as an agenda worth ([\d-]+) agenda point', line, re.UNICODE)
                stats['runner_score'] += int(point_value.group(3))
                stats['runner_agendas'][point_value.group(2)] = stats['runner_agendas'].get(point_value.group(2), 0) + 1
                if stats['runner_score'] >= 7:
                    stats['winner'] = True
                    stats['win_type'] = 0
            else:
                point_value = re.search(r' (scores|steals) ([&"\'!:\w\s-]+) and gains ([\d]+) agenda point', line, re.UNICODE)
                if point_value is None:
                    point_value = re.search(r'(adds) ([&"\'!:\w\s-]+) to their score area as an agenda worth ([\d-]+) agenda point', line, re.UNICODE)
                if point_value is None:
                    point_value = re.search(r'(uses) ([&"\'!:\w\s-]+) to add it to their score area and gain ([\d-]+) agenda point', line, re.UNICODE)
                stats['corp_score'] += int(point_value.group(3))
                stats['corp_agendas'][point_value.group(2)] = stats['corp_agendas'].get(point_value.group(2), 0) + 1
                if stats['corp_score'] >= 7:
                    stats['winner'] = False
                    stats['win_type'] = 0
        elif 'flatlined' in line:
            stats['winner'] = False
            stats['win_type'] = 1
        elif 'is decked' in line:
            stats['winner'] = True
            stats['win_type'] = 2
        elif 'concedes' in line:
            if runner_name in line:
                stats['winner'] = False
            else:
                stats['winner'] = True
            stats['win_type'] = 3
        else:
            continue
        fulltext += line

    fulltext = fulltext.strip()
    encoded_full = fulltext.encode('utf-8')
    stats['hash'] = hashlib.sha256(encoded_full).hexdigest()


    return stats

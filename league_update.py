import asyncio
from datetime import datetime, timedelta, timezone
import os
from time import sleep
import django
import requests
from discord_utils import discord_message_process, discord_message_process_with_channel
import urllib.parse


def score_to_acc(score, notes):
    max_score = 0
    multiply_count = 1
    while notes > 0 and multiply_count > 0:
        max_score += 115
        notes -= 1
        multiply_count -= 1
    multiply_count = 4
    while notes > 0 and multiply_count > 0:
        max_score += 115*2
        notes -= 1
        multiply_count -= 1
    multiply_count = 8
    while notes > 0 and multiply_count > 0:
        max_score += 115*4
        notes -= 1
        multiply_count -= 1
    while notes > 0:
        max_score += 115*8
        notes -= 1
    return score/max_score*100


def league_end_process(league, end, time_count):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbsl3.settings')
    django.setup()
    from app.models import Headline
    discord_message = f'{league} リーグが終了しました！'
    league.isLive = False
    playlist = league.playlist
    playlist.isEditable = False
    playlist.save()
    league.save()

    Headline.objects.create(player=None, time=end + timedelta(seconds=time_count), text=discord_message)
    time_count -= 1
    for i, winner in enumerate([league.first, league.second, league.third], start=1):
        if winner is not None:
            Headline.objects.create(player=winner, time=end + timedelta(seconds=time_count), text=f'{winner} さんが {i} 位！')
            discord_message += f'\n#{i} {winner} さん'
            time_count -= 1

    discord_message_process(discord_message)

def get_score_data(player, song):
    name_encode = urllib.parse.quote(player.name)
    url = f'https://scoresaber.com/api/leaderboard/by-id/{song.lid}/scores?countries=JP&search={name_encode}'
    res = requests.get(url).json()
    return res

def get_beatleader_data(player, song):
    sid = player.sid
    hash = song.hash
    diff = song.diff
    mode = song.char
    url = f'https://api.beatleader.xyz/score/{sid}/{hash}/{diff}/{mode}'
    res = requests.get(url)
    if res.status_code == 200:
        beatleader = res.json()['id']
        return beatleader
    return None

def update_score_internal(player, song, league, score, rawPP, miss, notes):
    from app.models import Score
    from app.views import score_to_acc, score_to_headline

    defaults = {
        'score': score,
        'acc': score_to_acc(score, int(notes)),
        'rawPP': rawPP,
        'miss': miss,
    }

    old_score = Score.objects.filter(player=player, song=song, league=league).first()
    if old_score and score <= old_score.score:
        print('already updated score')
        return
    
    beatleader = get_beatleader_data(player, song)
    if beatleader:
        defaults['beatleader'] = beatleader

    new_headline = None
    if league in player.league.all():
        new_headline = score_to_headline(score, song, player, league)
    
    new_score, check = Score.objects.update_or_create(
        player=player,
        song=song,
        league=league,
        defaults=defaults,
    )
    if new_headline:
        print("headline attached", new_headline)
        new_headline.score = new_score
        new_headline.save()
    print('score updated!')


def update_score(player, song, league, res):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbsl3.settings')
    django.setup()

    notes = song.notes
    for scoreData in res['scores']:
        hitname = scoreData['leaderboardPlayerInfo']['name']
        if player.name != hitname:
            print('wrong name!')
            continue

        score = scoreData['modifiedScore']
        rawPP = scoreData['pp']
        miss = scoreData['badCuts'] + scoreData['missedNotes']

        update_score_internal(player, song, league, score, rawPP, miss, notes)
        break

def create_headline(player, league, position):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbsl3.settings')
    django.setup()
    from app.models import Headline
    Headline.objects.create(
        player=player,
        time=datetime.now(),
        text=f'{player} さんが {league} リーグで {position} 位になりました！'
    )

def process_grand_slam(player, league):
    if player.theoretical == 100:
        valid_name = league.name.lower().replace(' ', '-').translate(str.maketrans("", "", "[]'.")) 
        discord_message_process_with_channel(f'{player} さんがグランドスラム達成！\n全部の有効譜面で 1 位です！', valid_name)


def league_update_process():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbsl3.settings')
    django.setup()
    from app.models import League, Score, Headline
    from app.views import calculate_scoredrank_LBs, score_to_headline
    time_count = 30
    for league in League.objects.filter(isLive=True):
        end = league.end
        now = datetime.now(timezone.utc)
        if now > end:
            print('end!')
            league_end_process(league, end, time_count)
            continue
        for player in league.player.all():
            print(player)
            for song in league.playlist.songs.all():
                print(song, song.lid)
                res = get_score_data(player, song)
                if 'errorMessage' in res:
                    print('no scoresaber data')

                    # beatleader_try
                    beatleader = get_beatleader_data(player, song)
                    if beatleader == None:
                        print('no beatleader data')
                        continue

                    url = f'https://api.beatleader.xyz/score/{player.sid}/{song.hash}/{song.diff}/{song.char}'
                    # print(url)
                    res = requests.get(url)
                    status_code = res.status_code
                    if status_code != 200:
                        continue
                    res = res.json()
                    # print(res)
                    score = int(res['modifiedScore'])
                    print(score)
                    defaults = {
                        'score': score,
                        'acc': float(res['accuracy'])*100,
                        'rawPP': 0,
                        'miss': int(res['missedNotes'] + int(res['badCuts'])),
                        'beatleader': res['id'],
                    }
                    headline = score_to_headline(score, song, player, league)
                    score_obj = Score.objects.update_or_create(
                        player=player,
                        song=song,
                        league=league,
                        defaults=defaults,
                    )[0]
                    if headline != None:
                        headline.score = score_obj
                        headline.save()
                    continue
                update_score(player, song, league, res)
        print(league)
        players, songs = calculate_scoredrank_LBs(league)
        for i, player in enumerate(players[:3]):
            if i == 0 and league.first != player:
                create_headline(player, league, i + 1)
                process_grand_slam(player, league)
                league.first = player
            elif i == 1 and league.second != player:
                create_headline(player, league, i + 1)
                league.second = player
            elif i == 2 and league.third != player:
                create_headline(player, league, i + 1)
                league.third = player
        league.save()


if __name__ == '__main__':
    league_update_process()

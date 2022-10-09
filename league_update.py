import asyncio
from datetime import datetime, timedelta, timezone
import os
from time import sleep
import django
import requests
from discord_utils import discord_message_process
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


def league_update_process():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbsl3.settings')
    django.setup()
    from app.models import League, Score, Headline
    from app.views import calculate_scoredrank_LBs, score_to_headline
    time_count = 30
    for league in League.objects.filter(isLive=True):
        end = league.end
        now = datetime.now(timezone.utc)
        print(end, now)
        if now > end:
            print('end')
            discord_message = ''
            league.isLive = False
            league.save()
            Headline.objects.create(
                player=None,
                time=end + timedelta(seconds=time_count),
                text=f'{league} リーグが終了しました！'
            )
            discord_message += f'{league} リーグが終了しました！'
            time_count -= 1
            if league.first != None:
                Headline.objects.create(
                    player=league.first,
                    time=end + timedelta(seconds=time_count),
                    text=f'{league.first} さんが 1 位！',
                )
                discord_message += f'\n#1 {league.first} さん'
                time_count -= 1
            if league.second != None:
                Headline.objects.create(
                    player=league.second,
                    time=end + timedelta(seconds=time_count),
                    text=f'{league.second} さんが 2 位！',
                )
                discord_message += f'\n#2 {league.second} さん'
                time_count -= 1
            if league.third != None:
                Headline.objects.create(
                    player=league.third,
                    time=end + timedelta(seconds=time_count),
                    text=f'{league.third} さんが 3 位！',
                )
                discord_message += f'\n#3 {league.third} さん'
                time_count -= 1
            discord_message_process(discord_message)
            continue
        for player in league.player.all():
            print(player)
            for song in league.playlist.songs.all():
                print(song, song.lid)
                name_encode = urllib.parse.quote(player.name)
                url = f'https://scoresaber.com/api/leaderboard/by-id/{song.lid}/scores?countries=JP&search={name_encode}'
                res = requests.get(url).json()
                if 'errorMessage' in res:
                    print('no score')
                    continue
                print(res)
                notes = song.notes
                for scoreData in res['scores']:
                    hitname = scoreData['leaderboardPlayerInfo']['name']
                    if player.name != hitname:
                        print('wrong name!')
                        continue
                    score = scoreData['modifiedScore']
                    rawPP = scoreData['pp']
                    miss = scoreData['badCuts'] + scoreData['missedNotes']
                    defaults = {
                        'score': score,
                        # 'acc': score/(115*8*int(notes)-7245)*100,
                        'acc': score_to_acc(score, int(notes)),
                        'rawPP': rawPP,
                        'miss': miss,
                    }
                    if league in player.league.all():
                        score_to_headline(score, song, player, league)
                    Score.objects.update_or_create(
                        player=player,
                        song=song,
                        league=league,
                        defaults=defaults,
                    )
                    print('score updated!')
                    break
        print(league)
        players, songs = calculate_scoredrank_LBs(league)
        for i, player in enumerate(players[:3]):
            if i == 0:
                if league.first != player:
                    Headline.objects.create(
                        player=player,
                        time=datetime.now(),
                        text=f'{player} さんが {league} リーグで 1 位になりました！'
                    )
                    if player.theoretical == 100:
                        discord_message_process(f'{player} さんがグランドスラム達成！\n全部の有効譜面で 1 位です！')
                league.first = player
            if i == 1:
                if league.second != player:
                    Headline.objects.create(
                        player=player,
                        time=datetime.now(),
                        text=f'{player} さんが {league} リーグで 2 位になりました！'
                    )
                league.second = player
            if i == 2:
                if league.third != player:
                    Headline.objects.create(
                        player=player,
                        time=datetime.now(),
                        text=f'{player} さんが {league} リーグで 3 位になりました！'
                    )
                league.third = player
        league.save()


if __name__ == '__main__':
    league_update_process()

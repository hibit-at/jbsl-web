from datetime import datetime, timedelta, timezone
import os
import django
import requests
from discord_message import discord_message_process


def league_update_process():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbsl3.settings')
    django.setup()
    from app.models import League, Score, Headline
    from app.views import calculate_scoredrank_LBs, score_to_headline
    time_count = 30
    for league in League.objects.filter(isLive=True):
        end = league.end
        now = datetime.now(timezone.utc)
        print(end,now)
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
                    time=end + timedelta(seconds=2),
                    text=f'{league.first} さんが 1 位！',
                )
                discord_message += f'\n#1 {league.first} さん'
                time_count -= 1
            if league.second != None:
                Headline.objects.create(
                    player=league.second,
                    time=end + timedelta(seconds=1),
                    text=f'{league.second} さんが 2 位！',
                )
                discord_message += f'\n#2 {league.second} さん'
                time_count -= 1
            if league.third != None:
                Headline.objects.create(
                    player=league.third,
                    time=end,
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
                url = f'https://scoresaber.com/api/leaderboard/by-id/{song.lid}/scores?countries=JP&search={player.name}'
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
                        'acc': score/(115*8*int(notes)-7245)*100,
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

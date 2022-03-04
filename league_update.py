from datetime import datetime
import os
import django
import requests


def league_update_process():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbsl3.settings')
    django.setup()
    from app.models import League, Score
    for league in League.objects.filter(end__gt=datetime.now()):
        for player in league.player.all():
            print(player)
            for song in league.playlist.songs.all():
                print(song, song.lid)
                url = f'https://scoresaber.com/api/leaderboard/by-id/{song.lid}/scores?search={player.name}'
                res = requests.get(url).json()
                if 'errorMessage' in res:
                    print('no score')
                    continue
                print(res)
                notes = song.notes
                scoreData = res['scores'][0]
                score = scoreData['modifiedScore']
                rawPP = scoreData['pp']
                miss = scoreData['badCuts'] + scoreData['missedNotes']
                defaults = {
                    'score': score,
                    'acc': score/(115*8*int(notes)-7245)*100,
                    'rawPP': rawPP,
                    'miss': miss,
                }
                Score.objects.update_or_create(
                    player=player,
                    song=song,
                    league=league,
                    defaults=defaults,
                )
                print('score updated!')


if __name__ == '__main__':
    league_update_process()

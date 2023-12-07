from datetime import datetime, timedelta, timezone
import os
from time import sleep
import django
import requests
from discord_utils import discord_message_process, discord_message_process_with_channel
import urllib.parse

def setup_django():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbsl3.settings')
    django.setup()
    
    
def league_end_process(league, time_count) -> str:
    from app.models import Headline
    discord_message = f'{league} リーグが終了しました！'
    league.isLive = False
    playlist = league.playlist
    playlist.isEditable = False
    playlist.save()
    league.save()
    record_time = datetime.now(timezone.utc)
    Headline.objects.create(player=None, time=record_time +timedelta(seconds=time_count), text=discord_message)
    time_count -= 1
    for i, winner in enumerate([league.first, league.second, league.third], start=1):
        if winner is not None:
            Headline.objects.create(
                player=winner, time=record_time + timedelta(seconds=time_count), text=f'{winner} さんが {i} 位！')
            discord_message += f'\n#{i} {winner} さん'
            time_count -= 1
    # discord の非同期関数対応のため、メッセージのリストを送り付けて一括で処理せざるを得ない
    # そのため、この関数では文字列も返すようにする
    return discord_message


def get_score_scoresaber(player, song):
    name_encode = urllib.parse.quote(player.name)
    url = f'https://scoresaber.com/api/leaderboard/by-id/{song.lid}/scores?countries=JP&search={name_encode}'
    res = requests.get(url).json()
    return res


def get_beatleader_bid(player, song):
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


def create_league_headline(player, league, position):
    from app.models import Headline
    Headline.objects.create(
        player=player,
        time=datetime.now(),
        text=f'{player} さんが {league} リーグで {position} 位になりました！'
    )


def notily_grand_slam(player, league):
    if player.theoretical == 100:
        content = f'{player} さんがグランドスラム達成！\n全部の有効譜面で 1 位です！'
        discord_message_process_with_channel(content, league.name)


def update_league_ranking(league):
    from app.operations import calculate_scoredrank_LBs
    players, songs = calculate_scoredrank_LBs(league)
    for i, player in enumerate(players[:3]):
        if i == 0 and league.first != player:
            create_league_headline(player, league, i + 1)
            notily_grand_slam(player, league)
            league.first = player
        elif i == 1 and league.second != player:
            create_league_headline(player, league, i + 1)
            league.second = player
        elif i == 2 and league.third != player:
            create_league_headline(player, league, i + 1)
            league.third = player
    league.save()




def update_score_internal(player, song, league, score, rawPP, miss, acc):
    from app.models import Score
    from app.operations import score_acc_to_headline

    defaults = {
        'score': score,
        'acc': acc,
        'rawPP': rawPP,
        'miss': miss,
    }

    old_score = Score.objects.filter(
        player=player, song=song, league=league).first()
    if old_score and score <= old_score.score:
        print('        already updated score')
        return

    beatleader = get_beatleader_bid(player, song)
    if beatleader:
        defaults['beatleader'] = beatleader

    new_headline = None
    if league in player.league.all():
        new_headline = score_acc_to_headline(score, acc, song, player, league)

    new_score, check = Score.objects.update_or_create(
        player=player,
        song=song,
        league=league,
        defaults=defaults,
    )
    if new_headline:
        print("        headline attached", new_headline)
        new_headline.score = new_score
        new_headline.save()
    print('        score updated!')



def update_score_by_beatleader(league,song,player):
    beatleader = get_beatleader_bid(player, song)
    if beatleader == None:
        print('        no beatleader data')
        return None
    url = f'https://api.beatleader.xyz/score/{player.sid}/{song.hash}/{song.diff}/{song.char}'
    res = requests.get(url)
    status_code = res.status_code
    if status_code != 200:
        print('        invalid request for BeatLeader')
        return None
    res = res.json()
    score = int(res['modifiedScore'])
    acc = float(res['accuracy'])*100*int(res['modifiedScore'])/int(res['baseScore'])
    print('       ',score,acc)
    rawPP = 0
    miss = int(res['missedNotes'] + int(res['badCuts']))
    beatleader = res['id']
    update_score_internal(player, song, league, score, rawPP, miss, acc)
    

def update_score_by_scoresaver(player, song, league, res):
    # res is a response from ScoreSaber
    from app.operations import score_to_acc

    notes = song.notes
    for scoreData in res['scores']:
        hitname = scoreData['leaderboardPlayerInfo']['name']
        if player.name != hitname:
            print('    wrong name!')
            continue

        score = scoreData['modifiedScore']
        rawPP = scoreData['pp']
        miss = scoreData['badCuts'] + scoreData['missedNotes']
        acc = score_to_acc(score, song.notes)
        print('       ',score,acc)

        update_score_internal(player, song, league, score, rawPP, miss, acc)
        break

def get_player_song_score(league, player):
    from app.models import Score
    from app.operations import score_to_headline
    print(player)
    for song in league.playlist.songs.all():
        print('   ',song, song.lid)
        res = get_score_scoresaber(player, song)
        if not 'errorMessage' in res:
            update_score_by_scoresaver(player, song, league, res)
        else:        
            print('        no scoresaber data')
            update_score_by_beatleader(league,song, player)



def league_update_process():
    setup_django()
    from app.models import League
    time_count = 30
    now = datetime.now(timezone.utc)
    
    # finish process
    finish_messages = []
    for league in League.objects.filter(isLive=True,end__lt=now).order_by('pk'):
        finish_messages.append(league_end_process(league, time_count))
        print(f'{league} has just finished!')
        time_count += 10
    if finish_messages:
        discord_message_process(finish_messages)
        
    # score update process
    for league in League.objects.filter(isLive=True,end__gte=now).order_by('end'):
        print(f'{league} started')
        for player in league.player.all():
            get_player_song_score(league, player)
        update_league_ranking(league)
        print(f'{league} ended\n')


if __name__ == '__main__':
    league_update_process()

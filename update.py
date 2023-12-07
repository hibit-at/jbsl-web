import os
import django
import requests
import sys

def update_player_info(specific=None):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbsl3.settings')
    django.setup()
    from app.views import top_score_registration
    from app.models import Player

    if specific:
        players = Player.objects.filter(isActivated=True, sid=specific)
    else:
        players = Player.objects.filter(isActivated=True).order_by('-borderPP')

    for player in players:
        top_score_registration(player)
        print(f'{player} updated!')
        print(player.sid)
        url = f'https://api.beatleader.xyz/player/{player.sid}?stats=true'
        res = requests.get(url)

        if res.status_code == 200:
            res = res.json()
            player.accPP = res['accPp']
            player.techPP = res['techPp']
            player.passPP = res['passPp']
            player.save()

def update_league_player_yurufuwa():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbsl3.settings')
    django.setup()
    from app.models import Player, League, Participant

    # initialize
    for player in Player.objects.filter(isActivated=True):
        player.yurufuwa = 0
        player.save()
    
    for league in League.objects.all():
        for player in league.player.all():
            player.yurufuwa += 1
            player.save()
        # for participant in Participant.objects.filter(league=league):
        #     print(participant)
        #     participant.player.yurufuwa += participant.count_pos
        #     participant.player.save()
        # league.owner.yurufuwa += 1
        league.owner.save()
        if league.first != None:
            league.first.yurufuwa += 3
            league.first.save()
        if league.second != None:
            league.second.yurufuwa += 2
            league.second.save()
        if league.third != None:
            league.third.yurufuwa += 1
            league.third.save()


if __name__ == '__main__':
    
    specific = None
    if len(sys.argv) > 1:
        specific = sys.argv[1]
        print(f'specific mode on {specific}')
        update_player_info(specific)
    else:
        update_player_info()

    update_league_player_yurufuwa()
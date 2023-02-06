import os
import django
import requests

def update_process():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbsl3.settings')
    django.setup()
    from app.views import top_score_registration
    from app.models import Player,League
    for player in Player.objects.filter(isActivated=True):
        top_score_registration(player)
        print(f'{player} updated!')
        
        print(player.sid)
        url = f'https://stage.api.beatleader.net/player/{player.sid}?stats=true'
        res = requests.get(url)

        if res.status_code == 200:

            res = res.json()
            print(res)
            player.accPP = res['accPp']
            player.techPP = res['techPp']
            player.passPP = res['passPp']
            player.save()
    
    # initialize

    for player in Player.objects.filter(isActivated=True):
        player.yurufuwa = 0
        player.save()
    
    for league in League.objects.all():
        for player in league.player.all():
            player.yurufuwa += 1
            player.save()
        league.owner.yurufuwa += 1
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
    update_process()
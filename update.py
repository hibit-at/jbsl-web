import os
import django


def update_process():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbsl3.settings')
    django.setup()
    from app.views import top_score_registration
    from app.models import Player,League
    for player in Player.objects.filter(isActivated=True):
        top_score_registration(player)
        print(f'{player} updated!')
    
    # initialize

    for player in Player.objects.filter(isActivated=True):
        player.yurufuwa = 0
        player.save()
    
    for league in League.objects.all():
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
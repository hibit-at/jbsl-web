import os
import django

def process():
    import sys
    cwd = os.getcwd()
    sys.path.append(cwd)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbsl3.settings')
    django.setup()
    from app.views import pos_acc_update
    from app.models import Playlist, Player, Song, League

    league_ids_str = input('input league ids or type "all"\n')
    if league_ids_str == 'all':
        matching_leagues = League.objects.all()
    else:
        league_ids = []
        for item in league_ids_str.split(','):
            if '-' in item:
                start, end = item.split('-')
                league_ids.extend(range(int(start), int(end) + 1))
            else:
                league_ids.append(int(item))
        matching_leagues = League.objects.filter(pk__in=league_ids)
    for league in matching_leagues:
        print(league)
        pos_acc_update(league.pk)

if __name__ == '__main__':
    process()

import os
import django


def update_process():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbsl3.settings')
    django.setup()
    from app.views import top_score_registration
    from app.models import Player
    for player in Player.objects.filter(isActivated=True):
        top_score_registration(player)
        print(f'{player} updated!')

if __name__ == '__main__':
    update_process()
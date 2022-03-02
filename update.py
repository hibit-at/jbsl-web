import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbsl3.settings')
django.setup()

from app.views import top_score_registration
from app.models import Player

for player in Player.objects.filter(isActivated=True):
    top_score_registration(player)
    print(f'{player} updated!')
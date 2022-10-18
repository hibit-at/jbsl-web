import os
import django
import sys

def process():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbsl3.settings')
    django.setup()
    from app.models import League
    for league in League.objects.filter(isLive=False):
        print(league)
        playlist = league.playlist
        if playlist == None:
            continue
        playlist.isEditable = False
        playlist.save()


if __name__ == '__main__':
    process()

import os
import django
import sys

def process():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbsl3.settings')
    django.setup()
    from app.models import Song
    for song in Song.objects.all():
        url = f'https://eu.cdn.beatsaver.com/{song.hash.lower()}.jpg'
        song.imageURL = url
        song.save()        

if __name__ == '__main__':
    process()

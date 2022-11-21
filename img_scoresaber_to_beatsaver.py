import os
import django
import sys

def process(pk):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbsl3.settings')
    django.setup()
    from app.models import Song, Playlist
    playlist = Playlist.objects.get(pk=pk)
    for song in playlist.songs.all():
        url = f'https://eu.cdn.beatsaver.com/{song.hash.lower()}.jpg'
        song.imageURL = url
        song.save()        

if __name__ == '__main__':
    args = sys.argv
    pk = int(args[1])
    process(pk)

import os
import django


def process(pk):
    import sys
    cwd = os.getcwd()
    sys.path.append(cwd)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbsl3.settings')
    django.setup()
    from app.models import Playlist
    playlist = Playlist.objects.get(pk=pk)
    for song in playlist.songs.all():
        url = f'https://eu.cdn.beatsaver.com/{song.hash.lower()}.jpg'
        song.imageURL = url
        song.save()


if __name__ == '__main__':
    print('input playlist ID.')
    pk = input()
    process(pk)

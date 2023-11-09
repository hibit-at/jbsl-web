import os
import django

def process():
    import sys
    cwd = os.getcwd()
    sys.path.append(cwd)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbsl3.settings')
    django.setup()
    from app.models import Playlist, Player, Song
    playlist_ids_str = input('input playlist ids\n')
    playlist_ids = [int(pid) for pid in playlist_ids_str.split(',')]
    matching_playlists = Playlist.objects.filter(pk__in=playlist_ids)
    for playlist in matching_playlists:
        print(playlist)
        for song in playlist.songs.all():
            song.isApplied = True
            song.save()
            print(f'{song} は応募譜面として登録されました')
            

if __name__ == '__main__':
    process()

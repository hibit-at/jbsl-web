import os
import django

def process():
    import sys
    cwd = os.getcwd()
    sys.path.append(cwd)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbsl3.settings')
    django.setup()
    from app.models import Playlist, Player
    playlist_ids_str = input('input playlist ids\n')
    playlist_ids = [int(pid) for pid in playlist_ids_str.split(',')]
    matching_playlists = Playlist.objects.filter(pk__in=playlist_ids)
    for playlist in matching_playlists:
        print(playlist)
    player_sids_str = input('input player sids\n')
    player_sids = [sid.strip() for sid in player_sids_str.split(',')]
    matching_players = Player.objects.filter(sid__in=player_sids)
    for player in matching_players:
        print(player)
    input('okay?')
    for playlist in matching_playlists:
        for player in matching_players:
            playlist.CoEditor.add(player)


if __name__ == '__main__':
    process()

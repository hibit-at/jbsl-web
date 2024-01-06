import os

import django

from utils import setup_django


def process():
    from app.models import Playlist

    playlist_ids_str = input("input playlist ids\n")
    playlist_ids = []
    for item in playlist_ids_str.split(","):
        if "-" in item:
            start, end = item.split("-")
            playlist_ids.extend(range(int(start), int(end) + 1))
        else:
            playlist_ids.append(int(item))
    matching_playlists = Playlist.objects.filter(pk__in=playlist_ids)
    for playlist in matching_playlists:
        print(playlist)
        for song in playlist.songs.all():
            song.isApplied = True
            song.save()
            print(f"{song} は応募譜面として登録されました")


if __name__ == "__main__":
    setup_django()
    process()

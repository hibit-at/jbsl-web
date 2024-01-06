import os
from datetime import datetime

import django
import pytz


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jbsl3.settings")
    django.setup()
    from app.models import League, Player, Playlist

    playlists = []

    for i in range(4):
        print(f"JBSL6 J{i+1} 予選")
        playlists.append(Playlist.objects.get(title=f"JBSL6 J{i+1} 予選"))

    print(playlists)

    leagues = []

    colors = [
        "rgba(220,130,250,.8)",
        "rgba(255,128,128,.8)",
        "rgba(255,255,128,.8)",
        "rgba(130,211,255,.8)",
    ]

    limits = [2000, 1150, 975, 800]

    for i in [3, 2, 1, 0]:
        playlist = playlists[i]
        league = League.objects.create(
            name=playlist.title,
            owner=Player.objects.get(name="hibit_at"),
            description=playlist.description,
            color=colors[i],
            max_valid=5,
            limit=limits[i],
            end=datetime(
                year=2023,
                month=11,
                day=5,
                hour=23,
                minute=59,
                tzinfo=pytz.timezone("Asia/Tokyo"),
            ),
            isOpen=True,
            isPublic=True,
            isLive=True,
            playlist=playlist,
            isOfficial=True,
            border_line=8,
        )
        leagues.append(league)

    for i in range(4):
        for j in range(4):
            if i == j:
                continue
            leagues[i].prohibited_leagues.add(leagues[j])


main()

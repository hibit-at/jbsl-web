import os
from datetime import datetime

import django
import pytz


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jbsl3.settings")
    django.setup()
    from app.models import League, Player, Playlist

    editor = Player.objects.get(name='hibit_at')
    print(editor)

    coeditors = []
    coeditors_name = [
        'Marsh_era','姚明#1747','がんばります | Gabriel','KTNR','zeon(じをん)','kinpatsu','komeijisan','okazu','aqui/takamitsu','yuzu-222','ささの',
    ]
    
    for name in coeditors_name:
        # print(name)
        coeditors.append(Player.objects.get(name=name))
    
    print(coeditors)
    
    playlist_title = [
        'JBSL8 Beginner',
        'JBSL8 J4 予選',
        'JBSL8 J3 予選',
        'JBSL8 J2 予選',
        'JBSL8 J1 予選',
        'JBSL8 J4 R1',
        'JBSL8 J3 R1',
        'JBSL8 J2 R1',
        'JBSL8 J1 R1',
        'JBSL8 J4 SF',
        'JBSL8 J4 GF',
        'JBSL8 J3 SF',
        'JBSL8 J3 GF',
        'JBSL8 J2 SF',
        'JBSL8 J2 GF',
        'JBSL8 J1 SF',
        'JBSL8 J1 GF',
    ]
    
    assert(len(playlist_title) == 17)
    
    for i in range(16):
        for j in range(i):
            assert(playlist_title[i] != playlist_title[j])
            
    for title in playlist_title:
        desc = title.split()[-1] + 'です！'
        print(desc)
        playlist = Playlist.objects.create(
            title = title,
            editor = editor,
            image = 'kari',
            description = desc,
            isEditable = True,
            isHidden = True
        )
        
        for coeditor in coeditors:
            playlist.CoEditor.add(coeditor)
        
        playlist.save()

def qualifier_open():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jbsl3.settings")
    django.setup()
    from app.models import League, Player, Playlist
    playlists = []

    for i in range(4):
        print(f"JBSL7 J{i+1} 予選")
        playlists.append(Playlist.objects.get(title=f"JBSL7 J{i+1} 予選"))

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
                year=2024,
                month=4,
                day=15,
                hour=0,
                minute=18,
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


def used_check():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jbsl3.settings")
    django.setup()
    from app.operations import check_used_song
    sample_url = 'https://beatsaver.com/maps/313a4'
    check_used_song(sample_url)

main()
# used_check()
# qualifier_open()


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
        'Marsh_era','がんばります | Gabriel','KTNR','zeon(じをん)','kinpatsu','komeijisan','okazu','aqui/takamitsu','yuzu-222','ささの',
    ]
    
    for name in coeditors_name:
        # print(name)
        coeditors.append(Player.objects.get(name=name))
    
    print(coeditors)
    
    playlist_title = [
        'JBSL9 J4 予選',
        'JBSL9 J3 予選',
        'JBSL9 J2 予選',
        'JBSL9 J1 予選',
        'JBSL9 J4 R1',
        'JBSL9 J3 R1',
        'JBSL9 J2 R1',
        'JBSL9 J1 R1',
        'JBSL9 J4 SF',
        'JBSL9 J4 GF',
        'JBSL9 J3 SF',
        'JBSL9 J3 GF',
        'JBSL9 J2 SF',
        'JBSL9 J2 GF',
        'JBSL9 J1 SF',
        'JBSL9 J1 GF',
    ]
    
    assert(len(playlist_title) == 16)
    
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
        print(f"JBSL9 J{i+1} 予選")
        playlists.append(Playlist.objects.get(title=f"JBSL9 J{i+1} 予選"))

    print(playlists)

    leagues = []

    colors = [
        "rgba(220,130,250,.8)",
        "rgba(255,128,128,.8)",
        "rgba(255,255,128,.8)",
        "rgba(130,211,255,.8)",
    ]

    limits = [2000, 1200, 1000, 800]

    for i in [3, 2, 1, 0]:
        playlist = playlists[i]
        playlist.isHidden = False
        playlist.save()
        league = League.objects.create(
            name=playlist.title,
            owner=Player.objects.get(name="hibit_at"),
            description=playlist.description,
            color=colors[i],
            max_valid=5,
            limit=limits[i],
            end=pytz.timezone('Asia/Tokyo').localize(
                datetime(2025,5,11,23,59)
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

# コピー処理を行うスクリプト
def copy_images_between_playlists(source_titles, target_titles):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jbsl3.settings")
    django.setup()
    from app.models import League, Player, Playlist
    
    if len(source_titles) != len(target_titles):
        raise ValueError("Source and target title lists must have the same length.")

    for source_title, target_title in zip(source_titles, target_titles):
        try:
            # source_title に対応するプレイリストを取得
            source_playlist = Playlist.objects.get(title=source_title)
            # target_title に対応するプレイリストを取得
            target_playlist = Playlist.objects.get(title=target_title)

            # image フィールドをコピー
            target_playlist.image = source_playlist.image
            target_playlist.save()  # 保存

            print(f"Copied image from {source_title} to {target_title}")
        except Playlist.DoesNotExist:
            print(f"Playlist with title {source_title} or {target_title} does not exist.")


source_titles = [
    "JBSL7 J1 GF",
    "JBSL7 J1 SF",
    "JBSL7 J2 GF",
    "JBSL7 J2 SF",
    "JBSL7 J3 GF",
    "JBSL7 J3 SF",
    "JBSL7 J4 GF",
    "JBSL7 J4 SF",
    "JBSL7 J1 R1",
    "JBSL7 J2 R1",
    "JBSL7 J3 R1",
    "JBSL7 J4 R1",
    "JBSL7 J1 予選",
    "JBSL7 J2 予選",
    "JBSL7 J3 予選",
    "JBSL7 J4 予選"
]

target_titles = [
    "JBSL9 J1 GF",
    "JBSL9 J1 SF",
    "JBSL9 J2 GF",
    "JBSL9 J2 SF",
    "JBSL9 J3 GF",
    "JBSL9 J3 SF",
    "JBSL9 J4 GF",
    "JBSL9 J4 SF",
    "JBSL9 J1 R1",
    "JBSL9 J2 R1",
    "JBSL9 J3 R1",
    "JBSL9 J4 R1",
    "JBSL9 J1 予選",
    "JBSL9 J2 予選",
    "JBSL9 J3 予選",
    "JBSL9 J4 予選"
]



# main()
# copy_images_between_playlists(source_titles,target_titles)
# used_check()
qualifier_open()


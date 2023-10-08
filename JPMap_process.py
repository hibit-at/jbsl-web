import os
import django
import sys
import requests
from calendar import monthrange
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from django.utils import timezone as django_timezone
import base64


def text_over(img, text, height, fontsize=36, text_color=(0, 0, 0, 0)):
    file = open("app/.fonts/meiryob.ttc", "rb")
    bytes_font = BytesIO(file.read())
    # ttfontname = "/app/.fonts/meiryob.ttc"
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(bytes_font, fontsize)
    textTopLeft = (30, height)
    draw.text(textTopLeft, text, fill=text_color, font=font)
    return img


division_colors = {
    0: (0, 0, 0, 255),  # 黒
    1: (200, 50, 200, 255),  # 紫
    2: (255, 128, 50, 255),  # 赤
    3: (200, 200, 0, 255),  # 黄
    4: (50, 50, 200, 255),  # 青
    # 他のdivisionに対しても色を追加できます
}

division_colors_transparent = {
    0: 'rgba(0, 0, 0, 255)',  # 黒
    1: 'rgba(220,130,250,.8)',  # 紫
    2: 'rgba(255,128,128,.8)',  # 赤
    3: 'rgba(255,255,128,.8)',  # 黄
    4: 'rgba(130,211,255,.8)',  # 青
    # 他のdivisionに対しても色を追加できます
}

division_borders = {
    0 : 2000,
    1 : 2000,
    2 : 1100,
    3 : 900,
    4 : 700,
}

def create_img(year=1000, month=13, div=0):
    canvasSize = (256, 256)
    backgroundRGB = (255, 255, 255, 255)
    img = Image.new('RGBA', canvasSize, backgroundRGB)
    img = text_over(img, 'JP Monthly', 50)
    img = text_over(img, f'{year} - {month}', 100)
    text_color = division_colors.get(div, (0, 0, 0, 255))
    img = text_over(img, f'Div. {div}', 150, 36, text_color=text_color)
    return img


def pil_to_base64(img, format="png"):
    buffer = BytesIO()
    img.save(buffer, format)
    img_str = base64.b64encode(buffer.getvalue()).decode("ascii")
    return img_str


def collect_maps(mapper, player=None):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbsl3.settings')
    django.setup()
    from app.models import JPMap
    if mapper == 0:
        return
    url = f'https://api.beatsaver.com/maps/uploader/{mapper}/0'
    res = requests.get(url).json()['docs']

    for r in res:
        name, bsr, hash, createdAt = r['name'], r['id'], r['versions'][0]['hash'], r['createdAt']
        try:
            time = datetime.strptime(createdAt, "%Y-%m-%dT%H:%M:%S.%fZ")
        except ValueError:
            time = datetime.strptime(createdAt, "%Y-%m-%dT%H:%M:%SZ")

        for d in r['versions'][0]['diffs']:
            nps, char, dif = d['nps'], d['characteristic'], d['difficulty']

            if not JPMap.objects.filter(hash=hash, diff=dif, char=char).exists():
                new_jpmap = JPMap.objects.create(
                    uploader=player,
                    name=name,
                    bsr=bsr,
                    hash=hash,
                    char=char,
                    diff=dif,
                    nps=nps,
                    createdAt=time,
                )
                print(new_jpmap)


def collect_by_player(player):
    collect_maps(player.mapper, player)


def collection():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbsl3.settings')
    django.setup()
    from app.models import Player
    for player in Player.objects.all():
        collect_maps(player.mapper, player)


def get_last_date(dt: datetime):
    dt = dt.replace(hour=23, minute=59, second=0, microsecond=0)
    return dt.replace(day=monthrange(dt.year, dt.month)[1])


def create_league(songs, start, last, division, superuser):
    print(division)
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbsl3.settings')
    django.setup()
    from app.models import Playlist, Song, League
    from app.views import create_song_by_hash, search_lid, diff_label_inv, char_dict_inv
    if len(songs) > 0:
        title = f"JP Monthly {start.year}-{start.month} Div.{division}"
        description = f'{start.year}-{start.month} の新着マップを自動収集したものです。'
        img = create_img(start.year, start.month, division)
        img_str = 'data:image/png;base64,' + pil_to_base64(img)
        playlist, created = Playlist.objects.update_or_create(
            title=title,
            defaults={
                'editor': superuser,
                'description': description,
                'image': img_str
            }
        )
        for song in songs:
            print(song)
            dif_num = diff_label_inv[song.diff]
            if song.char == 'Lightshow':
                continue
            gameMode = char_dict_inv[song.char]
            print(gameMode)
            if not Song.objects.filter(hash=song.hash, diff=song.diff, char=song.char).exists():
                lid = search_lid(song.hash, gameMode, dif_num)
                if lid == None:
                    print('no lid detected')
                    continue
            else:
                lid = Song.objects.get(
                    hash=song.hash, diff=song.diff, char=song.char).lid
            new_song = create_song_by_hash(song.hash, dif_num, song.char, lid)
            print(new_song)
            if new_song == None:
                continue
            playlist.songs.add(new_song)

        league, created = League.objects.update_or_create(
            name=playlist.title,
            defaults={
                'owner': superuser,
                'description': description,
                'color': division_colors_transparent[division],
                'max_valid': playlist.songs.count() // 2 + 1,
                'limit': division_borders[division],
                'end': last,
                'isOpen': True,
                'playlist': playlist,
            }
        )



def get_division(nps):
    if nps > 8:
        return 1
    elif nps > 6:
        return 2
    elif nps > 4:
        return 3
    else:
        return 4


def monthly():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbsl3.settings')
    django.setup()
    from app.models import JPMap, Player
    import pytz
    from django.conf import settings
    current_tz = pytz.timezone(settings.TIME_ZONE)
    now = datetime.now(current_tz)
    print(now)
    pre = now - timedelta(days=26)
    start = pre.replace(day=1, hour=0, minute=0)
    start_end = get_last_date(start)
    songs = {i: [] for i in range(1, 5)}
    song_hashes = {i: {} for i in range(1, 5)}

    for song in JPMap.objects.filter(createdAt__gte=start, createdAt__lte=start_end).order_by('-nps'):
        division = get_division(song.nps)
        if song.hash in song_hashes[division]:
            continue
        songs[division].append(song)
        song_hashes[division][song.hash] = 1

    superuser = Player.objects.get(sid=76561198405857645)
    last = get_last_date(now)
    print(last)

    for i in range(1, 5):
        create_league(songs[i], start, last, i, superuser)


def get_filtered_songs(start):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbsl3.settings')
    django.setup()
    from app.models import JPMap
    hashes = {}
    filtered_songs = []
    for song in JPMap.objects.filter(createdAt__gte=start).order_by('-nps'):
        if song.hash not in hashes:
            filtered_songs.append(song)
            hashes[song.hash] = 1
    return filtered_songs


def add_songs_to_playlist(playlist, songs):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbsl3.settings')
    django.setup()
    from app.models import Song
    from app.views import create_song_by_hash, search_lid, diff_label_inv, char_dict_inv
    for song in playlist.songs.all():
        playlist.songs.remove(song)

    for song in songs:
        dif_num = diff_label_inv[song.diff]
        if song.char == 'Lightshow':
            continue
        gameMode = char_dict_inv[song.char]
        if not Song.objects.filter(hash=song.hash, diff=song.diff, char=song.char).exists():
            lid = search_lid(song.hash, gameMode, dif_num)
            if lid is None:
                continue
        else:
            lid = Song.objects.get(
                hash=song.hash, diff=song.diff, char=song.char).lid
        new_song = create_song_by_hash(song.hash, dif_num, song.char, lid)
        playlist.songs.add(new_song)


def create_playlist(title, days):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbsl3.settings')
    django.setup()
    from app.models import Playlist
    now = django_timezone.now()
    start = now - timedelta(days=days)

    filtered_songs = get_filtered_songs(start)
    playlist = Playlist.objects.get(title=title)
    add_songs_to_playlist(playlist, filtered_songs)


def weekly():
    create_playlist('JP Weekly', 7)


def biweekly():
    create_playlist('JP Biweekly', 14)


def latest():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbsl3.settings')
    django.setup()
    from app.models import JPMap, Playlist, Player, Song, SongInfo
    from app.views import search_lid, create_song_by_hash, diff_label_inv, char_dict_inv
    playlist = Playlist.objects.get(title='JP Latest')

    playlist.songs.clear()

    song_order = 0

    for player in Player.objects.filter(mapper__gt=0).order_by('mapper_name'):
        print(player.mapper_name)

        for jmap in JPMap.objects.filter(uploader=player).order_by('-createdAt', '-char', '-nps'):
            print(jmap)
            dif_num = diff_label_inv[jmap.diff]
            if jmap.char == 'Lightshow':
                continue
            gameMode = char_dict_inv[jmap.char]
            song = Song.objects.filter(
                hash=jmap.hash, diff=jmap.diff, char=jmap.char).first()
            if song == None:
                lid = search_lid(jmap.hash, gameMode, dif_num)
                if lid is None:
                    print('no lid detected')
                    continue
                song = create_song_by_hash(jmap.hash, dif_num, jmap.char, lid)
                print(song)
            playlist.songs.add(song)
            defaults = {'order': song_order}
            SongInfo.objects.update_or_create(
                song=song,
                playlist=playlist,
                defaults=defaults,
            )
            song_order += 1
            break


if __name__ == '__main__':
    if len(sys.argv) > 1:
        eval(f'{sys.argv[1]}()')
    else:
        collection()
        weekly()
        biweekly()
        latest()

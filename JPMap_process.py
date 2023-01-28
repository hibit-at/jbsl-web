import os
import django
import sys
import requests
from datetime import datetime, timedelta
import calendar
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import base64


def text_over(img, text, height, fontsize=36):
    ttfontname = "./.fonts/meiryob.ttc"
    textRGB = (0, 0, 0, 0)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(ttfontname, fontsize)
    textTopLeft = (30, height)
    draw.text(textTopLeft, text, fill=textRGB, font=font)
    return img


def create_img(year=1000, month=13, div=0):
    canvasSize = (256, 256)
    backgroundRGB = (255, 255, 255, 255)
    img = Image.new('RGBA', canvasSize, backgroundRGB)
    img = text_over(img, 'JP Monthly', 50)
    img = text_over(img, f'{year} - {month}', 100)
    img = text_over(img, f'Div. {div}', 150)
    return img


def pil_to_base64(img, format="png"):
    buffer = BytesIO()
    img.save(buffer, format)
    img_str = base64.b64encode(buffer.getvalue()).decode("ascii")
    return img_str


def collect_by_player(player):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbsl3.settings')
    django.setup()
    from app.models import JPMap
    print(player.mapper)
    mapper = player.mapper
    if mapper > 0:
        url = f'https://api.beatsaver.com/maps/uploader/{mapper}/0'
        res = requests.get(url).json()['docs']
        print(res)
        for r in res:
            name = r['name']
            bsr = r['id']
            hash = r['versions'][0]['hash']
            # print(r['name'])
            createdAt = r['createdAt']
            # print(r['createdAt'])
            for d in r['versions'][0]['diffs']:
                # print(d)
                nps = d['nps']
                char = d['characteristic']
                dif = d['difficulty']
                print(name, createdAt, nps, char, dif)
                year = int(createdAt[0:4])
                month = int(createdAt[5:7])
                day = int(createdAt[8:10])
                hour = int(createdAt[11:13])
                minute = int(createdAt[14:16])
                print(year, month, day, hour, minute)
                time = datetime(year, month, day, hour, minute)
                if JPMap.objects.filter(hash=hash, diff=dif, char=char).exists():
                    print('exist!')
                    continue
                JPMap.objects.create(
                    uploader=player,
                    name=name,
                    bsr=bsr,
                    hash=hash,
                    char=char,
                    diff=dif,
                    nps=nps,
                    createdAt=time,
                )


def collection():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbsl3.settings')
    django.setup()
    from app.models import Player, JPMap
    for player in Player.objects.all():
        print(player.mapper)
        mapper = player.mapper
        if mapper > 0:
            url = f'https://api.beatsaver.com/maps/uploader/{mapper}/0'
            res = requests.get(url).json()['docs']
            print(res)
            for r in res:
                name = r['name']
                bsr = r['id']
                hash = r['versions'][0]['hash']
                # print(r['name'])
                createdAt = r['createdAt']
                # print(r['createdAt'])
                for d in r['versions'][0]['diffs']:
                    # print(d)
                    nps = d['nps']
                    char = d['characteristic']
                    dif = d['difficulty']
                    print(name, createdAt, nps, char, dif)
                    year = int(createdAt[0:4])
                    month = int(createdAt[5:7])
                    day = int(createdAt[8:10])
                    hour = int(createdAt[11:13])
                    minute = int(createdAt[14:16])
                    print(year, month, day, hour, minute)
                    time = datetime(year, month, day, hour, minute)
                    if JPMap.objects.filter(hash=hash, diff=dif, char=char).exists():
                        print('exist!')
                        continue
                    JPMap.objects.create(
                        uploader=player,
                        name=name,
                        bsr=bsr,
                        hash=hash,
                        char=char,
                        diff=dif,
                        nps=nps,
                        createdAt=time,
                    )


def monthly():
    def get_last_date(dt: datetime):
        return dt.replace(day=calendar.monthrange(dt.year, dt.month)[1])
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbsl3.settings')
    django.setup()
    from app.models import JPMap, Playlist, Player
    from app.views import create_song_by_hash, search_lid, diff_label_inv, char_dict_inv
    now = datetime.now()
    pre = now - timedelta(days=26)
    start = pre.replace(day=1)
    start_end = get_last_date(start)
    print(start, 'to', start_end)
    J3_songs = []
    J2_songs = []
    J1_songs = []
    J3_hash = {}
    J2_hash = {}
    J1_hash = {}
    for song in JPMap.objects.filter(createdAt__gte=start, createdAt__lte=start_end).order_by('-nps'):
        print(song, song.nps)
        if song.nps <= 4:
            if song.hash in J3_hash:
                continue
            J3_songs.append(song)
            J3_hash[song.hash] = 1
        elif song.nps <= 8:
            if song.hash in J2_hash:
                continue
            J2_songs.append(song)
            J2_hash[song.hash] = 1
        else:
            if song.hash in J1_hash:
                continue
            J1_songs.append(song)
            J1_hash[song.hash] = 1
    print(J3_songs)
    print(J2_songs)
    print(J1_songs)
    superuser = Player.objects.get(sid=76561198405857645)
    print(superuser)

    last = get_last_date(datetime.now())
    print(last)

    if len(J3_songs) > 0:
        title = f"JP Monthly {start.year}-{start.month} Div.3"
        description = f'{start.year}-{start.month} の新着マップを自動収集したものです。'
        print(title, description)
        img = create_img(start.year, start.month, 3)
        img_str = 'data:image/png;base64,' + pil_to_base64(img)
        print(img_str)
        playlist, check = Playlist.objects.update_or_create(
            title=title,
            editor=superuser,
            description=description,
            image=img_str,
        )
        for song in J3_songs:
            dif_num = diff_label_inv[song.diff]
            if song.char == 'Lightshow':
                continue
            gameMode = char_dict_inv[song.char]
            lid = search_lid(song.hash, gameMode, dif_num)
            if lid == None:
                print('no lid detected')
                continue
            print(lid)
            new_song = create_song_by_hash(song.hash, dif_num, song.char, lid)
            print(new_song)
            playlist.songs.add(new_song)

    if len(J2_songs) > 0:
        title = f"JP Monthly {start.year}-{start.month} Div.2"
        description = f'{start.year}-{start.month} の新着マップを自動収集したものです。'
        print(title, description)
        img = create_img(start.year, start.month, 2)
        img_str = 'data:image/png;base64,' + pil_to_base64(img)
        print(img_str)
        playlist, check = Playlist.objects.update_or_create(
            title=title,
            editor=superuser,
            description=description,
            image=img_str,
        )
        for song in J2_songs:
            dif_num = diff_label_inv[song.diff]
            if song.char == 'Lightshow':
                continue
            gameMode = char_dict_inv[song.char]
            lid = search_lid(song.hash, gameMode, dif_num)
            if lid == None:
                print('no lid detected')
                continue
            print(lid)
            new_song = create_song_by_hash(song.hash, dif_num, song.char, lid)
            print(new_song)
            playlist.songs.add(new_song)

    if len(J1_songs) > 0:
        title = f"JP Monthly {start.year}-{start.month} Div.1"
        description = f'{start.year}-{start.month} の新着マップを自動収集したものです。'
        print(title, description)
        img = create_img(start.year, start.month, 1)
        img_str = 'data:image/png;base64,' + pil_to_base64(img)
        print(img_str)
        playlist, check = Playlist.objects.update_or_create(
            title=title,
            editor=superuser,
            description=description,
            image=img_str,
        )
        for song in J1_songs:
            dif_num = diff_label_inv[song.diff]
            if song.char == 'Lightshow':
                continue
            gameMode = char_dict_inv[song.char]
            lid = search_lid(song.hash, gameMode, dif_num)
            if lid == None:
                print('no lid detected')
                continue
            print(lid)
            new_song = create_song_by_hash(song.hash, dif_num, song.char, lid)
            print(new_song)
            playlist.songs.add(new_song)


def weekly():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbsl3.settings')
    django.setup()
    from app.models import JPMap, Playlist, Player, Song
    from app.views import create_song_by_hash, search_lid, diff_label_inv, char_dict_inv
    now = datetime.now()
    start = now - timedelta(days=7)
    print(start, 'to')
    songs = []
    hashes = {}
    for song in JPMap.objects.filter(createdAt__gte=start).order_by('-nps'):
        print(song, song.nps)
        if song.hash in hashes:
            continue
        songs.append(song)
        hashes[song.hash] = 1
    print(songs)
    playlist = Playlist.objects.get(title='JP Weekly')
    print(playlist)
    for song in playlist.songs.all():
        playlist.songs.remove(song)
    for song in songs:
        print(song)
        dif_num = diff_label_inv[song.diff]
        print(dif_num)
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
        print(lid)
        new_song = create_song_by_hash(song.hash, dif_num, song.char, lid)
        print(new_song)
        playlist.songs.add(new_song)


def biweekly():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbsl3.settings')
    django.setup()
    from app.models import JPMap, Playlist, Player, Song
    from app.views import create_song_by_hash, search_lid, diff_label_inv, char_dict_inv
    now = datetime.now()
    start = now - timedelta(days=14)
    print(start, 'to')
    songs = []
    hashes = {}
    for song in JPMap.objects.filter(createdAt__gte=start).order_by('-nps'):
        print(song, song.nps)
        if song.hash in hashes:
            continue
        songs.append(song)
        hashes[song.hash] = 1
    print(songs)
    playlist = Playlist.objects.get(title='JP Biweekly')
    print(playlist)
    for song in playlist.songs.all():
        playlist.songs.remove(song)
    for song in songs:
        print(song)
        dif_num = diff_label_inv[song.diff]
        print(dif_num)
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
        print(lid)
        new_song = create_song_by_hash(song.hash, dif_num, song.char, lid)
        print(new_song)
        playlist.songs.add(new_song)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        eval(f'{sys.argv[1]}()')
    else:
        collection()
        monthly()

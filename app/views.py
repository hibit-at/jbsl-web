from collections import defaultdict
from datetime import datetime, timedelta
from io import BytesIO
import json
from django.urls import reverse
from django.http import HttpResponse
from django.shortcuts import render, redirect
from .models import League, LeagueComment, Player, Playlist, Song, Score, Headline, SongInfo
import requests
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.decorators import login_required
from django.db.models import Count

from PIL import Image
import base64


diff_label = {
    1: 'Easy',
    3: 'Normal',
    5: 'Hard',
    7: 'Expert',
    9: 'ExpertPlus',
}

diff_label_inv = {
    'Easy': 1,
    'Normal': 3,
    'Hard': 5,
    'Expert': 7,
    'ExpertPlus': 9,
}

char_dict = {
    'SoloStandard': 'Standard',
    'SoloLawless': 'Lawless',
}

char_dict_inv = {
    'Standard': 'SoloStandard',
    'Lawless': 'SoloLawless',
}

col_dict = {
    1: 'cyan',
    3: 'limegreen',
    5: 'orange',
    7: 'red',
    9: 'violet',
}

hmd_dict = {
    0: 'Unknown',
    1: 'Oculus Rift CV1',
    2: 'Vive',
    4: 'Vive Pro',
    8: 'Windows Mixed Reality',
    16: 'Rift S',
    32: 'Oculus Quest',
    64: 'Valve Index',
    128: 'Vive Cosmos',
}

league_colors = [
    {'value': 'lightblue', 'text': 'Blue'},
    {'value': 'lightgreen', 'text': 'Green'},
    {'value': 'lightsalmon', 'text': 'Orange'},
    {'value': 'lightpink', 'text': 'Red'},
    {'value': '#FFCCFF', 'text': 'Purple'},
    {'value': 'lightyellow', 'text': 'Yellow'},
]


def score_to_acc(score, notes):
    max_score = 0
    multiply_count = 1
    while notes > 0 and multiply_count > 0:
        max_score += 115
        notes -= 1
        multiply_count -= 1
    multiply_count = 4
    while notes > 0 and multiply_count > 0:
        max_score += 115*2
        notes -= 1
        multiply_count -= 1
    multiply_count = 8
    while notes > 0 and multiply_count > 0:
        max_score += 115*4
        notes -= 1
        multiply_count -= 1
    while notes > 0:
        max_score += 115*8
        notes -= 1
    return score/max_score*100


def slope(n):
    if n == 1:
        return 0
    if n == 2:
        return -3
    return -(n+2)


def index(request):
    params = {}
    user = request.user
    if user.is_authenticated:
        social = SocialAccount.objects.get(user=user)
        params['social'] = social
        player = user.player
        if player.isActivated:
            invitations = player.invite.all()
            params['invitations'] = invitations
    active_players = Player.objects.filter(
        isActivated=True).order_by('-borderPP')
    params['active_players'] = active_players
    if request.method == 'POST':
        post = request.POST
        print(post)
        if 'join' in post and post['join'] != '':
            join = post['join']
            league = League.objects.get(pk=join)
            league.player.add(player)
            league.invite.remove(player)
            return redirect('app:leaderboard', pk=league.pk)
        if 'decline' in post and post['decline'] != '':
            decline = post['decline']
            league = League.objects.get(pk=decline)
            league.invite.remove(player)
    headlines = Headline.objects.all().order_by('-time')[:10]
    params['headlines'] = headlines
    active_leagues = League.objects.filter(
        isOpen=True, isLive=True).order_by('end')
    params['active_leagues'] = active_leagues

    love_pair = 0
    love_sort = defaultdict(int)
    love_max = 0
    for player in active_players:
        if player.rival != None:
            love_sort[player.rival] += 1
            love_max = max(love_max, love_sort[player.rival])
            if player.rival.rival == player:
                love_pair += 1
    love_pair = int(love_pair/2)
    love_sort = [k for k, v in love_sort.items() if v == love_max]
    params['love_max'] = love_max
    params['love_pair'] = love_pair
    params['love_sort'] = love_sort

    return render(request, 'index.html', params)


def userpage(request, sid=0):
    params = {}
    user = request.user
    if user.is_authenticated:
        social = SocialAccount.objects.get(user=user)
        params['social'] = social
    if not Player.objects.filter(sid=sid).exists():
        return redirect('app:index')
    player = Player.objects.get(sid=sid)
    params['player'] = player
    if request.method == 'POST':
        post = request.POST
        print(post)
        if 'imageURL' in post:
            imageURL = post['imageURL']
            if imageURL.startswith('https://pbs.twimg.com/profile_images'):
                player.imageURL = imageURL
        if 'message' in post:
            player.message = post['message'][:50]
        if 'twitter' in post:
            player.twitter = post['twitter']
        if 'twitch' in post:
            player.twitch = post['twitch']
        if 'booth' in post:
            player.booth = post['booth']
        if 'rival' in post:
            rival_sid = post['rival']
            rival = Player.objects.get(sid=rival_sid)
            user.player.rival = rival
            user.player.save()
        if 'icon_scoresaber' in post:
            player.imageURL = f'https://cdn.scoresaber.com/avatars/{player.sid}.jpg'
        if 'icon_discord' in post:
            if social.extra_data['avatar'] != None:
                player.imageURL = f'https://cdn.discordapp.com/avatars/{social.uid}/{social.extra_data["avatar"]}'
        if 'color' in post:
            userColor = post['color']
            player.userColor = userColor
        if 'bg' in post:
            bgColor = post['bg']
            player.bgColor = bgColor
        if 'shadow' in post:
            player.isShadow = True
        else:
            player.isShadow = False
        player.save()
    eyebeam = Player.objects.filter(rival=player).count()
    print(eyebeam)
    params['eyebeam'] = eyebeam
    top10 = Score.objects.filter(
        player=player, league__name='Top10').order_by('-rawPP')
    params['top10'] = top10

    return render(request, 'userpage.html', params)


@login_required
def mypage(request):
    user = request.user
    social = SocialAccount.objects.get(user=user)
    params = {}
    params['social'] = social
    # player registartion
    if not Player.objects.filter(user=user).exists():
        player = Player.objects.create(user=user)
        player.discordID = social.uid
        player.save()
    # registration end
    if not user.player.isActivated:
        return render(request, 'activation.html', params)
    player = user.player
    return redirect('app:userpage', sid=player.sid)


def create_song_by_hash(hash, diff_num, char, lid):
    if Song.objects.filter(lid=lid).exists():
        return Song.objects.get(lid=lid)
    url = f'https://api.beatsaver.com/maps/hash/{hash}'
    res = requests.get(url).json()
    if 'error' in res:
        return None
    bsr = res['id']
    title = res['name']
    author = res['uploader']['name']
    versions = res['versions']
    latest = versions[0]
    diffs = latest['diffs']
    diff = diff_label[diff_num]
    color = col_dict[diff_num]
    imageURL = f"https://cdn.scoresaber.com/covers/{str(hash).upper()}.png"
    notes = 0
    for diff_data in diffs:
        if diff_data['difficulty'] == diff and diff_data['characteristic'] == char:
            notes = diff_data['notes']
    print(bsr, title, author, diff, notes)
    Song.objects.create(
        title=title,
        author=author,
        diff=diff,
        char=char,
        notes=notes,
        bsr=bsr,
        hash=hash,
        lid=lid,
        color=color,
        imageURL=imageURL,
    )
    return Song.objects.get(lid=lid)


def score_to_headline(new_score, song, player, league):
    title = song.title
    tail = ''
    if len(title) > 30:
        tail = '...'
    title = title[:30] + tail
    if Score.objects.filter(player=player, song=song, league=league).exists():
        old_score = Score.objects.get(player=player, song=song, league=league)
        if new_score > old_score.score:
            old_acc = old_score.acc
            # new_acc = new_score/(115*8*int(song.notes)-7245)*100
            new_acc = score_to_acc(new_score, song.notes)
            Headline.objects.create(
                player=player,
                time=datetime.now(),
                text=f'{player} さんが {title} ({song.diff}) のスコアを更新！ {old_acc:.2f} -> {new_acc:.2f} %'
            )
    else:
        # new_acc = new_score/(115*8*int(song.notes)-7245)*100
        new_acc = score_to_acc(new_score, song.notes)
        Headline.objects.create(
            player=player,
            time=datetime.now(),
            text=f'{player} さんが {title} ({song.diff}) のスコアを更新！ {new_acc:.2f} %'
        )


def top_score_registration(player):
    sid = player.sid
    # pp
    url = f'https://scoresaber.com/api/player/{sid}/basic'
    res = requests.get(url).json()
    if 'errorMessage' in res:
        return
    pp = res['pp']
    name = res['name']
    player.pp = pp
    player.name = name
    player.save()
    # top10
    url = f'https://scoresaber.com/api/player/{sid}/scores?limit=10&sort=top'
    res = requests.get(url).json()
    playerScores = res['playerScores']
    # initialize
    league = League.objects.get(name='Top10')
    for score in Score.objects.filter(league=league, player=player):
        score.delete()
    # add
    for playerScore in playerScores:
        leaderboard = playerScore['leaderboard']
        lid = leaderboard['id']
        hash = leaderboard['songHash']
        diff_num = leaderboard['difficulty']['difficulty']
        gameMode = leaderboard['difficulty']['gameMode']
        char = char_dict[gameMode]
        if not Song.objects.filter(lid=lid).exists():
            create_song_by_hash(hash, diff_num, char, lid)
        song = Song.objects.get(lid=lid)
        notes = song.notes
        score = playerScore['score']['modifiedScore']
        pp = playerScore['score']['pp']
        miss = playerScore['score']['missedNotes'] + \
            playerScore['score']['badCuts']
        hmd = hmd_dict[playerScore['score']['hmd']]
        if hmd != 'Unknown' or player.hmd == 'Unknown':
            player.hmd = hmd
        defaults = {
            'score': score,
            # 'acc': score/(115*8*int(notes)-7245)*100,
            'acc': score_to_acc(score, notes),
            'rawPP': pp,
            'miss': miss,
        }
        # score_to_headline(score, song, player, league)
        print(defaults)
        Score.objects.update_or_create(
            player=player,
            song=song,
            league=league,
            defaults=defaults,
        )
    # if over erase
    top10 = Score.objects.filter(
        player=player, league__name='Top10').order_by('-rawPP')
    if len(top10) > 10:
        print('over')
        for over_score in top10[10:]:
            over_score.delete()
    # border pp calc
    border_pp = 0
    for t in top10[1:4]:
        border_pp += t.rawPP
    player.borderPP = border_pp
    player.save()
    return


@login_required
def activate_process(request):
    user = request.user
    player = user.player
    if player.isActivated:
        return redirect('app:mypage')
    params = {}
    social = SocialAccount.objects.get(user=user)
    params['social'] = social
    if request.method == 'POST':
        url = request.POST.get('url')
        print(url)
        sid = url.split('/')[-1]
        print(sid)
        # basic information
        url = f'https://scoresaber.com/api/player/{sid}/basic'
        res = requests.get(url).json()
        if res['country'] != 'JP':
            params['error'] = '日本人以外のプレイヤーは登録できません。Sorry, Only Japanese player can be registered.'
            return render(request, 'activation.html', params)
        name = res['name']
        imageURL = res['profilePicture']
        pp = res['pp']
        player.name = name
        player.sid = sid
        player.imageURL = imageURL
        player.isActivated = True
        player.pp = pp
        player.save()
        text = f'{player} さんが参加しました！　JBSLへようこそ！'
        Headline.objects.create(
            player=player,
            text=text,
            time=datetime.now()
        )
        # top score registration
        top_score_registration(player)
        return redirect('app:mypage')
    return render(request, 'activation.html', params)


def song(request, lid=0):
    params = {}
    song = Song.objects.get(lid=lid)
    user = request.user
    if user.is_authenticated:
        social = SocialAccount.objects.get(user=user)
        params['social'] = social
    params['song'] = song
    return render(request, 'song.html', params)


def search_lid(hash, gameMode, diff_num):
    url = f'https://scoresaber.com/api/leaderboard/get-difficulties/{hash}'
    res = requests.get(url).json()
    if 'errorMessage' in res:
        return False
    for r in res:
        if r['difficulty'] != diff_num:
            continue
        if r['gameMode'] != gameMode:
            continue
        return r['leaderboardId']


def add_playlist(playlist, json_data):
    for song in json_data['songs']:
        hash = song['hash']
        print(song)
        if 'difficulties' not in song:
            continue
        difficulty = song['difficulties'][0]
        char = difficulty['characteristic']
        gameMode = char_dict_inv[char]
        diff = difficulty['name']
        diff = diff[0].upper() + diff[1:]
        print(diff)
        if not Song.objects.filter(hash=hash, diff=diff, char=char).exists():
            diff_num = diff_label_inv[diff]
            if search_lid(hash, gameMode, diff_num) == False:
                continue
            lid = search_lid(hash, gameMode, diff_num)
            create_song_by_hash(hash, diff_num, char, lid)
        if not Song.objects.filter(hash=hash, diff=diff, char=char).exists():
            continue
        song_object = Song.objects.get(hash=hash, diff=diff, char=char)
        playlist.songs.add(song_object)
        print(hash, char, diff)


@login_required
def create_playlist(request):
    params = {}
    user = request.user
    social = SocialAccount.objects.get(user=user)
    params['social'] = social
    if request.method == 'POST':
        post = request.POST
        print(post)
        if 'playlist' in post and post['playlist'] == '':
            params['error'] = 'ERROR : プレイリストファイルが存在しません。'
            return render(request, 'create_playlist.html', params)
        if 'playlist' in request.FILES:
            json_data = json.load(request.FILES['playlist'].file)
            title = json_data['playlistTitle']
            image = json_data['image']
            if image.startswith('base64'):
                image = 'data:image/png;' + image
            description = ''
            if 'playlistDescription' in json_data:
                description = json_data['playlistDescription']
            editor = request.user.player
            isEditable = False
            if 'editable' in request.POST:
                isEditable = True
            if Playlist.objects.filter(title=title).exists():
                params['error'] = 'ERROR : すでに同名のプレイリストが存在します。'
                return render(request, 'create_playlist.html', params)
            Playlist.objects.create(
                title=title,
                editor=editor,
                image=image,
                description=description,
                isEditable=isEditable,
            )
            print(title, editor)
            playlist = Playlist.objects.get(title=title)
            playlist.save()
            add_playlist(playlist, json_data)
            print(playlist.title)
            print(playlist.songs.all())
            return redirect('app:playlists')
        if 'title' in post:
            title = post['title']
            description = post['description']
            if title == '' or description == '':
                params['error'] = 'ERROR : タイトルと説明文の両方を記入してください。'
                return render(request, 'create_playlist.html', params)
            if Playlist.objects.filter(title=title).exists():
                params['error'] = 'ERROR : すでに同名のプレイリストが存在します。'
                return render(request, 'create_playlist.html', params)
            editor = request.user.player
            isEditable = True
            url = 'https://4.bp.blogspot.com/-ZHlXgooA38A/Wn1WVe2XBhI/AAAAAAABKJY/5BE6ZAbyeRwv3UlGsVU2YfPWVS_uT0PFQCLcBGAs/s800/text_kakko_kari.png'
            img = Image.open(BytesIO(requests.get(url).content))
            width, height = img.size
            new_img = Image.new(img.mode, (width, width), (0, 0, 0, 0))
            new_img.paste(img, (0, width//4))
            buffer = BytesIO()
            new_img.save(buffer, 'png')
            img_str = base64.b64encode(buffer.getvalue()).decode('ascii')
            playlist = Playlist.objects.create(
                title=title,
                editor=editor,
                description=description,
                isEditable=isEditable,
                image='data:image/png;base64,' + img_str
            )
            return redirect('app:playlist', pk=playlist.pk)

    return render(request, 'create_playlist.html', params)


def make_sorted_playlists(playlists):
    playlist_songs = defaultdict(list)
    for playlist in playlists:
        for song in playlist.songs.all():
            print(playlist, song)
            if SongInfo.objects.filter(song=song, playlist=playlist).exists():
                songinfo = SongInfo.objects.get(song=song, playlist=playlist)
                setattr(song, 'order', songinfo.order)
            else:
                SongInfo.objects.create(
                    song=song,
                    playlist=playlist,
                )
                setattr(song, 'order', 0)
            playlist_songs[playlist].append(song)
        print(type(playlist_songs[playlist]))
        playlist_songs[playlist] = sorted(
            playlist_songs[playlist], key=lambda x: x.order)
        print(playlist)
        print(playlist_songs[playlist])
    for playlist in playlists:
        setattr(playlist, 'playlist_songs', playlist_songs[playlist])
    return playlists


def playlists(request):
    params = {}
    user = request.user
    if user.is_authenticated:
        social = SocialAccount.objects.get(user=user)
        params['social'] = social
    playlists = Playlist.objects.all().order_by('-pk')
    # playlists = make_sorted_playlists(playlists)
    params['playlists'] = playlists
    return render(request, 'playlists.html', params)


def make_sorted_playlist(playlist):
    sorted_songs = []
    for song in playlist.songs.all():
        if SongInfo.objects.filter(song=song, playlist=playlist).exists():
            songinfo = SongInfo.objects.get(song=song, playlist=playlist)
            setattr(song, 'order', songinfo.order)
        else:
            SongInfo.objects.create(
                song=song,
                playlist=playlist,
            )
            setattr(song, 'order', 0)
        sorted_songs.append(song)
    sorted_songs = sorted(sorted_songs, key=lambda x: x.order)
    setattr(playlist, 'sorted_songs', sorted_songs)
    return playlist


def playlist(request, pk):
    params = {}
    user = request.user
    playlist = Playlist.objects.get(pk=pk)

    # leagues
    leagues = League.objects.filter(playlist=playlist)
    print(leagues)
    params['leagues'] = leagues

    # reorder
    if user.is_authenticated:
        if playlist.editor == user.player:
            playlist = make_sorted_playlist(playlist)
            for i, song in enumerate(playlist.sorted_songs):
                print(song)
                songInfo = SongInfo.objects.get(song=song, playlist=playlist)
                songInfo.order = i
                songInfo.save()

    if user.is_authenticated:
        social = SocialAccount.objects.get(user=user)
        params['social'] = social
        isEditor = (user.player == playlist.editor)
        params['isEditor'] = isEditor
    if request.method == 'POST':
        post = request.POST
        files = request.FILES
        print(post)
        print(files)
        if 'add_song' in post and post['add_song'] != '':
            lid = post['add_song'].split('/')[-1]
            url = f'https://scoresaber.com/api/leaderboard/by-id/{lid}/info'
            res = requests.get(url).json()
            hash = res['songHash']
            diff_num = res['difficulty']['difficulty']
            gameMode = res['difficulty']['gameMode']
            char = char_dict[gameMode]
            song = create_song_by_hash(hash, diff_num, char, lid)
            if song is not None:
                playlist.songs.add(song)
                # if not SongInfo.objects.filter(song=song,playlist=playlist).exists():
                SongInfo.objects.update_or_create(
                    song=song,
                    playlist=playlist,
                    defaults={'order': playlist.songs.all().count()},
                )
                playlist.recommend.remove(song)
        if 'recommend_song' in post and post['recommend_song'] != '':
            lid = post['recommend_song'].split('/')[-1]
            url = f'https://scoresaber.com/api/leaderboard/by-id/{lid}/info'
            res = requests.get(url).json()
            hash = res['songHash']
            diff_num = res['difficulty']['difficulty']
            gameMode = res['difficulty']['gameMode']
            char = char_dict[gameMode]
            song = create_song_by_hash(hash, diff_num, char, lid)
            if song is not None:
                playlist.recommend.add(song)
        if 'remove_song' in post and post['remove_song'] != '':
            lid = post['remove_song']
            song = Song.objects.get(lid=lid)
            playlist.songs.remove(song)
        if 'remove_recommend' in post and post['remove_recommend'] != '':
            lid = post['remove_recommend']
            song = Song.objects.get(lid=lid)
            playlist.recommend.remove(song)
        if 'description' in post and post['description'] != '':
            description = post['description']
            playlist.description = description[:100]
            playlist.save()
        if 'image' in files:
            image = Image.open(request.FILES['image'].file)
            image = image.resize((128, 128))
            buffer = BytesIO()
            image.save(buffer, 'png')
            img_str = base64.b64encode(buffer.getvalue()).decode('ascii')
            playlist.image = 'data:image/png;base64,' + img_str
            playlist.save()
        if 'remove_playlist' in post and post['remove_playlist'] != '':
            confirm = post['confirm']
            title = post['remove_playlist']
            print(confirm, title)
            if confirm == title:
                playlist.delete()
                return redirect('app:playlists')
        if 'editable' in post:
            playlist.isEditable = not playlist.isEditable
            playlist.save()
        if 'title' in post and post['title'] != '':
            title = post['title']
            playlist.title = title
            playlist.save()
        if 'up' in post:
            lid = post['up']
            song = Song.objects.get(lid=lid)
            songInfo = SongInfo.objects.get(song=song, playlist=playlist)
            songInfo.order -= 1
            songInfo.save()
            # swap
            for swapped_song in SongInfo.objects.filter(playlist=playlist, order=songInfo.order):
                print(swapped_song)
                swapped_song.order += 1
                swapped_song.save()
            songInfo.save()
        if 'down' in post:
            lid = post['down']
            song = Song.objects.get(lid=lid)
            songInfo = SongInfo.objects.get(song=song, playlist=playlist)
            songInfo.order += 1
            # swap
            for swapped_song in SongInfo.objects.filter(playlist=playlist, order=songInfo.order):
                print(swapped_song)
                swapped_song.order -= 1
                swapped_song.save()
            songInfo.save()
    playlist = make_sorted_playlist(playlist)
    params['playlist'] = playlist

    return render(request, 'playlist.html', params)


def download_playlist(request, pk):
    json_data = {}
    playlist = Playlist.objects.get(pk=pk)
    playlist = make_sorted_playlist(playlist)
    json_data['playlistTitle'] = playlist.title
    json_data['playlistAuthor'] = 'JBSL_Web_System'
    json_data['playlistDescription'] = playlist.description
    songs = []
    for song in playlist.sorted_songs:
        append_dict = {}
        append_dict['songName'] = song.title
        append_dict['levelAuthorName'] = song.author
        append_dict['hash'] = song.hash
        difficulties = []
        diff_append = {}
        diff_append['characteristic'] = song.char
        diff_append['name'] = song.diff
        difficulties.append(diff_append)
        append_dict['difficulties'] = difficulties
        songs.append(append_dict)
    json_data['songs'] = songs
    json_data['image'] = playlist.image
    download_data = json.dumps(json_data, ensure_ascii=False)
    return HttpResponse(download_data)


def leagues(request):
    params = {}
    user = request.user
    if user.is_authenticated:
        social = SocialAccount.objects.get(user=user)
        params['social'] = social
    active_leagues = League.objects.filter(
        isOpen=True, isLive=True).order_by('end')
    end_leagues = League.objects.filter(
        isOpen=True, isLive=False).order_by('-end')
    params['active_leagues'] = active_leagues
    params['end_leagues'] = end_leagues
    return render(request, 'leagues.html', params)


def calculate_scoredrank_LBs(league, virtual=None):
    # リーグ内プレイヤーの人数
    base = league.player.count() + 3
    # リーグ内マップ
    playlist = league.playlist
    playlist = make_sorted_playlist(playlist)
    songs = league.playlist.sorted_songs
    # プレイヤーごとのスコア
    total_rank = defaultdict(list)
    # マップごとのプレイヤーランキング
    from django.db.models import Q
    for song in songs:
        query = Score.objects.filter(
            song=song, league=league).filter(Q(player__league=league) | Q(player=virtual)).order_by('-score').distinct()
        for rank, score in enumerate(query):
            pos = base + slope(rank + 1)
            setattr(score, 'rank', rank+1)
            setattr(score, 'pos', pos)
            player = score.player
            total_rank[player].append(score)
        setattr(song, 'scores', query)
    # 順位点→精度でソート
    for t in total_rank:
        total_rank[t] = sorted(total_rank[t], key=lambda x: (-x.pos, -x.acc))
    # 有効範囲の分だけ合算する
    players = []
    count_range = league.method
    for player, score_list in total_rank.items():
        score_list = score_list[:count_range]
        for score in score_list:
            setattr(score, 'valid', 'O')
        valid_count = len(score_list)
        max_pos = league.method * (base + slope(1))
        count_pos = sum([s.pos for s in score_list])
        theoretical = count_pos / max_pos * 100
        count_acc = sum([s.acc for s in score_list])/valid_count
        tooltip_pos = '<br>'.join(
            [f'{score.song.title[:25]}... ({score.pos})' for score in score_list])
        tooltip_valid = '<br>'.join(
            [f'{score.song.title[:25]}...' for score in score_list])
        tooltip_acc = '<br>'.join(
            [f'{score.song.title[:25]}... ({score.acc:.2f})' for score in score_list])
        setattr(player, 'count_pos', count_pos)
        setattr(player, 'theoretical', theoretical)
        setattr(player, 'count_acc', count_acc)
        setattr(player, 'valid', valid_count)
        setattr(player, 'tooltip_pos', tooltip_pos)
        setattr(player, 'tooltip_valid', tooltip_valid)
        setattr(player, 'tooltip_acc', tooltip_acc)
        if LeagueComment.objects.filter(league=league, player=player).exists():
            comment = LeagueComment.objects.get(league=league, player=player)
            setattr(player, 'comment', comment)
        players.append(player)
    # 順位点→精度でソート
    players = sorted(
        players, key=lambda x: (-x.count_pos, -x.count_acc))
    for rank, player in enumerate(players):
        setattr(player, 'rank', rank+1)
    return players, songs


def leaderboard(request, pk):
    params = {}
    user = request.user
    if user.is_authenticated:
        social = SocialAccount.objects.get(user=user)
        params['social'] = social
    league = League.objects.get(pk=pk)
    params['league'] = league
    scored_rank, LBs = calculate_scoredrank_LBs(league)
    params['scored_rank'] = scored_rank
    params['LBs'] = LBs

    isMember = False
    isOwner = False
    isVirtual = False
    if user.is_authenticated:
        if user.player in league.player.all():
            isMember = True
        if user.player == league.owner:
            isOwner = True
        if user.player in league.virtual.all():
            isVirtual = True

    params['isOwner'] = isOwner
    params['isMember'] = isMember
    params['isVirtual'] = isVirtual

    end_str = (league.end + timedelta(hours=9)).strftime('%Y-%m-%dT%H:%M')
    params['end_str'] = end_str

    # POST

    if request.method == 'POST':
        post = request.POST
        print(post)
        if 'join' in post and post['join'] != '':
            sid = post['join']
            add_player = Player.objects.get(sid=sid)
            league.player.add(add_player)
            return redirect('app:leaderboard', pk=pk)
        if 'disjoin' in post and post['disjoin'] != '':
            sid = post['disjoin']
            remove_player = Player.objects.get(sid=sid)
            league.player.remove(remove_player)
            return redirect('app:leaderboard', pk=pk)
        if 'invite' in post:
            invites = post.getlist('invite')
            for invite in invites:
                invite_player = Player.objects.get(sid=invite)
                league.invite.add(invite_player)
        if 'title' in post:
            league.name = post['title']
            if post['description'] != '':
                league.description = post['description']
            league.end = datetime.strptime(post['end'], '%Y-%m-%dT%H:%M')
            league.method = post['valid']
            league.limit = post['limit']
            league.save()
            return redirect('app:leaderboard', pk=pk)

    not_invite_players = Player.objects.exclude(
        league=league).exclude(invite=league).filter(isActivated=True).order_by('-borderPP')
    params['not_invite_players'] = not_invite_players

    from datetime import timezone

    close_line = league.end - timedelta(days=2)
    isClose = datetime.now(timezone.utc) >= close_line and league.isOfficial
    print(isClose)
    params['isClose'] = isClose

    return render(request, 'leaderboard.html', params)


@login_required
def create_league(request):
    get = request.GET
    params = {}
    if 'pk' in get:
        print(get['pk'])
        params['select'] = int(get['pk'])
        print(type(params['select']))
    user = request.user
    social = SocialAccount.objects.get(user=user)
    params['social'] = social
    default_end = datetime.now() + timedelta(days=14)
    default_end_str = default_end.strftime('%Y-%m-%dT%H:%M')
    params['default_end_str'] = default_end_str
    playlists = Playlist.objects.all().filter(editor=user.player)
    playlists = playlists.annotate(num_of_songs=Count('songs'))
    playlists = playlists.filter(num_of_songs__lte=20)
    params['playlists'] = playlists
    params['league_colors'] = league_colors
    if request.method == 'POST':
        post = request.POST
        print(post)
        playlist_pk = post['playlist']
        title = post['title']
        description = post['description']
        color = post['color']
        end = datetime.strptime(post['end'], '%Y-%m-%dT%H:%M')
        isPublic = ('public' in post)
        limit = post['limit']
        valid = post['valid']
        playlist = Playlist.objects.get(pk=playlist_pk)
        if len(playlist.songs.all()) > 20:
            params['error'] = 'プレイリストの曲数が多すぎます。上限は 20 です。'
            return render(request, 'create_league.html', params)
        league = League.objects.create(
            name=title,  # 名称の不一致。余裕があれば後で直す。
            owner=user.player,
            description=description,
            color=color,
            end=end,
            playlist=playlist,
            method=valid,  # 名称の不一致。余裕があれば後で直す。
            isPublic=isPublic,
            isOpen=True,
            limit=limit,
        )
        return redirect('app:leaderboard', pk=league.pk)
    return render(request, 'create_league.html', params)


@login_required
def virtual_league(request, pk):
    params = {}
    user = request.user
    player = user.player
    if user.is_authenticated:
        social = SocialAccount.objects.get(user=user)
        params['social'] = social
    league = League.objects.get(pk=pk)
    for song in league.playlist.songs.all():
        print(song, song.lid)
        url = f'https://scoresaber.com/api/leaderboard/by-id/{song.lid}/scores?countries=JP&search={player.name}'
        res = requests.get(url).json()
        if 'errorMessage' in res:
            print('no score')
            continue
        print(res)
        notes = song.notes
        for scoreData in res['scores']:
            hitname = scoreData['leaderboardPlayerInfo']['name']
            if player.name != hitname:
                print('wrong name!')
                continue
            score = scoreData['modifiedScore']
            rawPP = scoreData['pp']
            miss = scoreData['badCuts'] + scoreData['missedNotes']
            defaults = {
                'score': score,
                # 'acc': score/(115*8*int(notes)-7245)*100,
                'acc': score_to_acc(score, notes),
                'rawPP': rawPP,
                'miss': miss,
            }
            if league in player.league.all():
                score_to_headline(score, song, player, league)
            Score.objects.update_or_create(
                player=player,
                song=song,
                league=league,
                defaults=defaults,
            )
            print('score updated!')
    params['league'] = league
    scored_rank, LBs = calculate_scoredrank_LBs(league, user.player)
    params['scored_rank'] = scored_rank
    params['LBs'] = LBs

    return render(request, 'virtual_league.html', params)


@login_required
def rivalpage(request):
    params = {}
    user = request.user
    social = SocialAccount.objects.get(user=user)
    params['social'] = social
    player = user.player
    params['player'] = player
    songs = Song.objects.all()
    compares = []
    match = 0
    win = 0
    for song in songs:
        my_scores = song.score.filter(player=player).order_by('-score')
        rival_scores = song.score.filter(
            player=player.rival).order_by('-score')
        if len(my_scores) > 0 and len(rival_scores) > 0:
            match += 1
            print(my_scores)
            print(rival_scores)
            my_top = my_scores[0]
            rival_top = rival_scores[0]
            if my_top.score >= rival_top.score:
                compares.append({
                    'your': my_top,
                    'rival': rival_top,
                    'win': True
                })
                win += 1
            else:
                compares.append({
                    'your': my_top,
                    'rival': rival_top,
                    'win': False
                })
    print(compares)
    params['compares'] = compares
    params['match'] = match
    params['win'] = win
    params['lose'] = match - win

    # POST

    if request.method == 'POST':
        post = request.POST
        print(post)
        if 'no_rival' in post:
            user.player.rival = None
            user.player.save()
            return redirect('app:mypage')
    return render(request, 'rivalpage.html', params)


def headlines(request, page=1):
    params = {}
    user = request.user
    if user.is_authenticated:
        social = SocialAccount.objects.get(user=user)
        params['social'] = social
    start = (page-1) * 100
    end = page * 100
    headlines = Headline.objects.all().order_by('-time')[start:end]
    params['headlines'] = headlines
    params['old'] = page + 1
    params['page'] = page
    params['new'] = page - 1
    return render(request, 'headlines.html', params)


def players(request):
    params = {}
    user = request.user
    if user.is_authenticated:
        social = SocialAccount.objects.get(user=user)
        params['social'] = social
        player = user.player
        if player.isActivated:
            invitations = player.invite.all()
            params['invitations'] = invitations
    active_players = Player.objects.filter(
        isActivated=True).order_by('-borderPP')
    params['active_players'] = active_players
    return render(request, 'players.html', params)


def debug(request):
    if not request.user.is_staff:
        return redirect('app:index')
    active_players = Player.objects.filter(isActivated=True).order_by('-pp')
    params = {}
    params['active_players'] = active_players
    for player in active_players:
        check = defaultdict(int)
        print(player)
        rivals = []
        if player.rival == None:
            continue
        rival = player
        while True:
            check[rival] += 1
            if check[rival] > 1:
                rivals.append(rival)
                break
            print('...', rival)
            rivals.append(rival)
            if rival.rival == None:
                break
            rival = rival.rival
        setattr(player, 'rivals', rivals[1:])

    return render(request, 'debug.html', params)


def api_leaderboard(request, pk):
    params = {}
    league = League.objects.get(pk=pk)
    params['league'] = league
    scored_rank, LBs = calculate_scoredrank_LBs(league)
    ans = {}
    ans['league_id'] = pk
    ans['league_title'] = league.name
    ans['total_rank'] = []
    for i, rank in enumerate(scored_rank):
        ans['total_rank'].append({
            'standing': i+1,
            'sid': rank.sid,
            'name': rank.name,
            'pos': rank.count_pos,
        })
        print(rank.name)
    ans['maps'] = []
    for LB in LBs:
        append_score = []
        for i, score in enumerate(LB.scores):
            append_score.append({
                'standing': i+1,
                'sid': score.player.sid,
                'name': score.player.name,
                'acc': score.acc,
                'pos': score.pos,
            })
        ans['maps'].append({
            'title': LB.title,
            'lid': LB.lid,
            'bsr': LB.bsr,
            'scores': append_score,
        })
    return HttpResponse(json.dumps(ans, indent=4, ensure_ascii=False))


def bsr_checker(request):
    params = {}
    user = request.user
    if user.is_authenticated:
        social = SocialAccount.objects.get(user=user)
        params['social'] = social
    if request.method == 'POST':
        post = request.POST
        print(post)

        class Result:

            def __init__(self, text, link) -> None:
                self.text = text
                self.link = link

            def __str__(self) -> str:
                return str(self.text)

        class Results:

            def __init__(self) -> None:
                self.results = []

            def append(self, text, link=None):
                append_res = Result(text, link)
                self.results.append(Result(text, link))

            def __str__(self) -> str:
                return ','.join(map(str, self.results))

        results = Results()
        twitchURL = post['twitchURL']
        twitchID = twitchURL.split('/')[-1]
        results.append(f'検出された Twitch ID : {twitchID}')
        if not Player.objects.filter(twitch=twitchID).exists():
            results.append(f'! JBSL Web にマッチするプレイヤーがいません。')
            params['results'] = results
            return render(request, 'bsr_checker.html', params)
        player = Player.objects.get(twitch=twitchID)
        results.append(
            f'マッチするプレイヤー：{player.name}', f'https://jbsl-web.herokuapp.com/userpage/{player.sid}')
        results.append(f'Score Saber : {player.sid}',
                       f'https://scoresaber.com/u/{player.sid}')
        params['results'] = results
        bsr = post['bsr_command'].split(' ')[-1].split('/')[-1]
        results.append(f'検出された bsr key : {bsr}')
        url = f'https://api.beatsaver.com/maps/id/{bsr}'
        res = requests.get(url).json()
        print(res)
        if not 'versions' in res:
            results.append(f'! bsr key から正しい譜面情報を取得できませんでした。')
            params['results'] = results
            return render(request, 'bsr_checker.html', params)
        title = res['name']
        res = res['versions'][0]
        hash = res['hash']
        results.append(f'hash : {hash} ({title})')
        diffs = res['diffs']
        for i, diff in enumerate(diffs):
            chara = diff['characteristic']
            label = diff['difficulty']
            notes = diff['notes']
            chara_scoresaber = char_dict_inv[chara]
            diff_scoresaber = diff_label_inv[label]
            print(chara_scoresaber, diff_scoresaber)
            url = f'https://scoresaber.com/api/leaderboard/by-hash/{hash}/info?difficulty={diff_scoresaber}&gameMode={chara_scoresaber}'
            res = requests.get(url).json()
            if not 'id' in res:
                results.append(f'! ScoreSaber から譜面の情報を取得することができませんでした。')
                continue
            lid = res['id']
            results.append(f'diff {i+1} {chara} {label} リーダーボード ID : {lid}',
                           f'https://scoresaber.com/leaderboard/{lid}?search={player.name}')
            url = f'https://scoresaber.com/api/leaderboard/by-id/{lid}/scores?countries=JP&search={player.name}'
            res = requests.get(url).json()
            if not 'scores' in res:
                results.append(f'...No Score')
                continue
            res = res['scores'][0]
            timeSet = res['timeSet']
            date = datetime.strptime(
                timeSet.split('.')[0], '%Y-%m-%dT%H:%M:%S')
            date += timedelta(hours=9)
            print(date)
            time_dif = datetime.now() - date
            if time_dif.days > 1:
                when = f'{time_dif.days} 日前'
            else:
                when = f'{time_dif.seconds//60:,} 分前'
            score = res['modifiedScore']
            acc = score/(115*8*int(notes)-7245)*100
            results.append(f'...{when} に {acc:,.2f} %のスコアが登録されています。')
        print(results)
        params['results'] = results.results

    return render(request, 'bsr_checker.html', params)


def coin(request):
    league = request.GET.get('league')
    league = League.objects.get(pk=league)
    params = {'league': league}
    participants = Player.objects.all().filter(
        league=league).order_by('borderPP').reverse()
    choice = []
    for p in participants:
        choice.append((p.sid, p.name))

    from django import forms

    class CoinForm(forms.Form):
        partA = forms.ChoiceField(
            label='選手1', widget=forms.Select, choices=choice, required=False)
        partB = forms.ChoiceField(
            label='選手2', widget=forms.Select, choices=choice, required=False)

    import random

    form = CoinForm()
    result = ''
    if request.method == 'POST':
        post = request.POST
        partA = Player.objects.get(sid=post['partA'])
        partB = Player.objects.get(sid=post['partB'])
        print(partA)
        print(partB)
        form = CoinForm(post)
        if partA == partB:
            result = '同じ選手が選択されています。違う選手を選択してください。'
        else:
            if random.random() > 0.5:
                result = f'コイントスの結果、{partA} さんがファーストピックの権利を得ました。BANは {partB} さんからです。'
            else:
                result = f'コイントスの結果、{partB} さんがファーストピックの権利を得ました。BANは {partA} さんからです。'
    params['form'] = form
    params['result'] = result
    return render(request, 'coin.html', params)


def info(request):
    params = {}
    user = request.user
    if user.is_authenticated:
        social = SocialAccount.objects.get(user=user)
        params['social'] = social
    return render(request, f'info.html', params)


def info2(request):
    params = {}
    user = request.user
    if user.is_authenticated:
        social = SocialAccount.objects.get(user=user)
        params['social'] = social
    return render(request, f'info2.html', params)


def info3(request):
    params = {}
    user = request.user
    if user.is_authenticated:
        social = SocialAccount.objects.get(user=user)
        params['social'] = social
    return render(request, f'info3.html', params)


def info4(request):
    params = {}
    user = request.user
    if user.is_authenticated:
        social = SocialAccount.objects.get(user=user)
        params['social'] = social
    return render(request, f'info4.html', params)


def info5(request):
    params = {}
    user = request.user
    if user.is_authenticated:
        social = SocialAccount.objects.get(user=user)
        params['social'] = social
    return render(request, f'info5.html', params)


def info6(request):
    params = {}
    user = request.user
    if user.is_authenticated:
        social = SocialAccount.objects.get(user=user)
        params['social'] = social
    return render(request, f'info6.html', params)


@login_required
def score_comment(request):
    user = request.user
    social = SocialAccount.objects.get(user=user)
    params = {}
    params['social'] = social
    print(request.method)
    if request.method == "POST":
        post = request.POST
        print(post)
        score = Score.objects.get(pk=post['score'])
        if 'comment' in post:
            score.comment = post['comment']
            score.save()
            redirect_url = reverse('app:leaderboard', args=[score.league.pk])
            print(redirect_url)
            return redirect(f'{redirect_url}#{score.song.lid}')
        print(score)
        params['score'] = score
        return render(request, 'score_comment.html', params)
    return redirect('app:index')


@login_required
def league_comment(request):
    user = request.user
    social = SocialAccount.objects.get(user=user)
    params = {}
    params['social'] = social
    print(request.method)
    print('league comment')
    if request.method == "POST":
        post = request.POST
        print(post)
        print('hoge')
        league = League.objects.get(pk=post['league'])
        player = Player.objects.get(pk=post['player'])
        params['league'] = league
        params['player'] = player
        print(league)
        print(player)
        if 'comment' in post:
            comment = post['comment'][:50]
            defaults = {'message': comment}
            LeagueComment.objects.update_or_create(
                league=league,
                player=user.player,
                defaults=defaults,
            )
            return redirect('app:leaderboard', pk=league.pk)
        if LeagueComment.objects.filter(league=league, player=player).exists():
            comment = LeagueComment.objects.get(league=league, player=player)
            setattr(player, 'comment', comment)
        return render(request, 'league_comment.html', params)
    return redirect('app:index')

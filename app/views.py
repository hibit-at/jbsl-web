from collections import defaultdict
from datetime import datetime, timedelta
from io import BytesIO
import json
from django.http import HttpResponse
from django.shortcuts import render, redirect
from .models import League, Player, Playlist, Song, Score
import requests
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.decorators import login_required

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
    {'value': '#FF99FF', 'text': 'Purple'},
    {'value': 'lightyellow', 'text': 'Yellow'},
]


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
    return render(request, 'index.html', params)


def userpage(request, sid=0):
    params = {}
    user = request.user
    if user.is_authenticated:
        social = SocialAccount.objects.get(user=user)
        params['social'] = social
        isSelf = (int(user.player.sid) == sid)
        params['isSelf'] = isSelf
    if not Player.objects.filter(sid=sid).exists():
        return redirect('app:index')
    player = Player.objects.get(sid=sid)
    params['player'] = player
    if request.method == 'POST':
        post = request.POST
        if 'message' in post:
            player.message = post['message'][:50]
        if 'twitter' in post:
            player.twitter = post['twitter']
        if 'twitch' in post:
            player.twitch = post['twitch']
        if 'booth' in post:
            player.booth = post['booth']
        player.save()
    top10 = Score.objects.filter(
        player=player, league__name='Top10').order_by('-rawPP')
    params['top10'] = top10

    # リーグ参加

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
    imageURL = f"https://scoresaber.com/imports/images/songs/{hash}.png"
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


def top_score_registration(player):
    sid = player.sid
    # pp
    url = f'https://scoresaber.com/api/player/{sid}/basic'
    res = requests.get(url).json()
    pp = res['pp']
    player.pp = pp
    player.save()
    # top10
    url = f'https://scoresaber.com/api/player/{sid}/scores?limit=10&sort=top'
    res = requests.get(url).json()
    playerScores = res['playerScores']
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
        player.hmd = hmd
        defaults = {
            'score': score,
            'acc': score/(115*8*int(notes)-7245)*100,
            'rawPP': pp,
            'miss': miss,
        }
        print(defaults)
        Score.objects.update_or_create(
            player=player,
            song=song,
            league=League.objects.get(name='Top10'),
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
                image='base64,' + img_str
            )
            return redirect('app:playlist', pk=playlist.pk)

    return render(request, 'create_playlist.html', params)


def playlists(request):
    params = {}
    user = request.user
    if user.is_authenticated:
        social = SocialAccount.objects.get(user=user)
        params['social'] = social
    playlists = Playlist.objects.all()
    params['playlists'] = playlists
    return render(request, 'playlists.html', params)


def playlist(request, pk):
    params = {}
    user = request.user
    playlist = Playlist.objects.get(pk=pk)
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
    params['playlist'] = playlist
    return render(request, 'playlist.html', params)


def download_playlist(request, pk):
    json_data = {}
    playlist = Playlist.objects.get(pk=pk)
    json_data['playlistTitle'] = playlist.title
    json_data['playlistAuthor'] = 'JBSL_Web_System'
    json_data['playlistDescription'] = playlist.description
    songs = []
    for song in playlist.songs.all():
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


@login_required
def add_song_to_playlist(request, pk, url):
    user = request.user
    playlist = Playlist.objects.get(pk=pk)
    if user.player != playlist.editor:
        return redirect('index.html')
    lid = url.split('/')[-1]
    print(lid)
    return


def leagues(request):
    params = {}
    user = request.user
    if user.is_authenticated:
        social = SocialAccount.objects.get(user=user)
        params['social'] = social
    active_leagues = League.objects.filter(isOpen=True)
    for league in active_leagues:
        scored_rank, LBs = calculate_scoredrank_LBs(league)
        setattr(league, 'top_players', scored_rank[:3])
    params['active_leagues'] = active_leagues
    return render(request, 'leagues.html', params)


def calculate_scoredrank_LBs(league):
    # リーグ内プレイヤー
    players = league.player.all()
    size = len(players)
    base = size + 3
    # リーグ内マップ
    songs = league.playlist.songs.all()
    # マップごとのプレイヤーランキング
    # LBs = []
    total_rank = defaultdict(list)
    for song in songs:
        query = Score.objects.filter(
            song=song, league=league, player__league=league).order_by('-score')
        for rank, score in enumerate(query):
            pos = base + slope(rank + 1)
            setattr(score, 'rank', rank+1)
            setattr(score, 'pos', pos)
            player = score.player
            total_rank[player].append(score)
        setattr(song, 'scores', query)
        # LBs.append({'song': song, 'scores': query})
    print(songs)
    # 順位点→精度でソート
    for t in total_rank:
        total_rank[t] = sorted(total_rank[t], key=lambda x: (-x.pos, -x.score))
    # 有効範囲の分だけ合算する
    counted_rank = []
    count_range = league.method
    for player, score_list in total_rank.items():
        score_list = score_list[:count_range]
        valid_count = len(score_list)
        count_pos = sum([s.pos for s in score_list])
        count_acc = sum([s.acc for s in score_list])
        setattr(player, 'count_pos', count_pos)
        setattr(player, 'count_acc', count_acc)
        setattr(player, 'valid', valid_count)
        setattr(player, 'count_maps', score_list)
        counted_rank.append(player)
    counted_rank = sorted(counted_rank, key=lambda x: (-x.count_pos, -x.count_acc))
    for rank, counted in enumerate(counted_rank):
        setattr(counted, 'rank', rank+1)
    return counted_rank, songs


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
    if user.is_authenticated:
        if user.player in league.player.all():
            isMember = True
        if user.player == league.owner:
            isOwner = True

    params['isOwner'] = isOwner
    params['isMember'] = isMember

    end_str = (league.end + timedelta(hours=9)).strftime('%Y-%m-%dT%H:%M')
    print(league.end)
    print(end_str)
    params['end_str'] = end_str

    # POST

    if request.method == 'POST':
        post = request.POST
        print(post)
        if 'join' in post and post['join'] != '':
            sid = post['join']
            add_player = Player.objects.get(sid=sid)
            league.player.add(add_player)
            return redirect('app:leaderboard', pk=league.pk)
        if 'disjoin' in post and post['disjoin'] != '':
            sid = post['disjoin']
            add_player = Player.objects.get(sid=sid)
            league.player.remove(add_player)
            return redirect('app:leaderboard', pk=league.pk)
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
            return redirect('app:leaderboard', pk=league.pk)

    not_invite_players = Player.objects.exclude(
        league=league).exclude(invite=league).order_by('-borderPP')
    params['not_invite_players'] = not_invite_players

    return render(request, 'leaderboard.html', params)


@login_required
def create_league(request):
    params = {}
    user = request.user
    social = SocialAccount.objects.get(user=user)
    params['social'] = social
    default_end = datetime.now() + timedelta(days=14)
    default_end_str = default_end.strftime('%Y-%m-%dT%H:%M')
    params['default_end_str'] = default_end_str
    playlists = Playlist.objects.all()
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

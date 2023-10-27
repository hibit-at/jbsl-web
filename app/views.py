import base64
import json
import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from io import BytesIO
from time import time
from typing import Dict, List, Any

import requests
from PIL import Image
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Max
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone as django_timezone

from .models import League, Participant, Player, Playlist, Song, Score, Headline, SongInfo, Badge, Match, DGA, User


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
    'SoloOneSaber': 'OneSaber',
    'Solo90Degree': '90Degree',
    'Solo360Degree': '360Degree',
    'SoloNoArrows': 'NoArrows',
}

char_dict_inv = {
    'Standard': 'SoloStandard',
    'Lawless': 'SoloLawless',
    'OneSaber': 'SoloOneSaber',
    '90Degree': 'Solo90Degree',
    '360Degree': 'Solo360Degree',
    'NoArrows': 'SoloNoArrows',
}

col_dict = {
    1: 'rgba(130,211,255,.8)',
    3: 'rgba(128,255,128,.8)',
    5: 'rgba(255,128,60,.8)',
    7: 'rgba(255,128,128,.8)',
    9: 'rgba(220,130,250,.8)',
}

hmd_dict = {
    0: 'Unknown',
    1: 'Oculus Rift CV1',
    2: 'Vive',
    4: 'Vive Pro',
    8: 'Windows Mixed Reality',
    16: 'Rift S',
    32: 'Oculus Quest',
    61: 'Quest Pro',
    64: 'Valve Index',
    128: 'Vive Cosmos',
    256: 'Quest 2',
}

league_colors = [
    {'value': 'rgba(130,211,255,.8)', 'text': 'Blue'},
    {'value': 'rgba(128,255,128,.8)', 'text': 'Green'},
    {'value': 'rgba(255,128,60,.8)', 'text': 'Orange'},
    {'value': 'rgba(255,128,128,.8)', 'text': 'Red'},
    {'value': 'rgba(220,130,250,.8)', 'text': 'Purple'},
    {'value': 'rgba(255,255,128,.8)', 'text': 'Yellow'},
]


def get_decorate(acc: float) -> str:
    if acc < 50:
        return 'color:dimgray'
    if 95 <= acc < 96:
        return 'font-weight:bold;text-shadow: 1px 1px 0 deepskyblue'
    if 96 <= acc < 97:
        return 'font-weight:bold;text-shadow: 1px 1px 0 mediumseagreen'
    if 97 <= acc < 98:
        return 'font-weight:bold;text-shadow: 1px 1px 0 orange'
    if 98 <= acc < 99:
        return 'font-weight:bold;text-shadow: 1px 1px 0 tomato'
    if 99 <= acc <= 100:
        return 'font-weight:bold;text-shadow: 1px 1px 0 violet'
    return 'None'


def score_to_acc(score: float, notes: int) -> float:
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


def slope(n: int) -> int:
    if n == 1:
        return 0
    if n == 2:
        return -3
    return -(n+2)


def validation(s: str) -> str:
    ans = ''
    for c in s:
        if b'\xc2\x80' <= c.encode('utf-8') and c.encode('utf-8') <= b'\xd4\xbf':
            continue
        ans += c
    return ans


def get_love_pair_context(active_players) -> Dict[str, Any]:
    context = {}
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
    context['love_max'] = love_max
    context['love_pair'] = love_pair
    context['love_sort'] = love_sort
    return context


def get_headline_and_league_context() -> Dict[str, Any]:
    context = {}
    headlines = Headline.objects.all().order_by('-time')[:8]
    context['headlines'] = headlines
    active_leagues = League.objects.filter(
        isOpen=True, isLive=True).order_by('-isOfficial', 'end', '-pk')
    context['active_leagues'] = active_leagues
    return context


def index(request) -> HttpResponse:
    context = {}
    user = request.user
    if user.is_authenticated:
        social = SocialAccount.objects.get(user=user)
        context['social'] = social
        if not Player.objects.filter(user=user).exists():
            return redirect('app:mypage')
        player = user.player
        if player.isActivated:
            all_invitations = player.invite.all()
            invitations = []
            for league in all_invitations:
                if player in league.player.all():
                    continue
                if not league.isLive:
                    continue
                invitations.append(league)
            context['invitations'] = invitations
    # active_players = Player.objects.filter(
    #     isActivated=True).order_by('-borderPP')
    # context['active_players'] = active_players
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
            return redirect('app:index')
    context.update(get_headline_and_league_context())
    # context.update(get_love_pair_context(context['active_players']))
    return render(request, 'index.html', context)


def process_mapper(post, player: Player, context):
    mapper_id = post['mapper']
    if mapper_id == '':
        player.mapper = 0
        player.mapper_name = ''
    elif Player.objects.filter(mapper=mapper_id).exists():
        context['mapper_error'] = '! 既にマッパーとして登録されています。もし自分以外のプレイヤーがなりすましている場合は、管理者 hibit までお知らせください。 !'
    else:
        url = f'https://api.beatsaver.com/users/id/{mapper_id}'
        mapper_name = requests.get(url).json()['name']
        player.mapper = int(mapper_id)
        player.mapper_name = mapper_name
        player.save()
        import sys
        sys.path.append('../')
        import JPMap_process
        JPMap_process.collect_by_player(player)


def userpage(request, sid=0):
    context = {}
    user = request.user
    if user.is_authenticated:
        social = SocialAccount.objects.get(user=user)
        context['social'] = social
    if not Player.objects.filter(sid=sid).exists():
        return redirect('app:index')
    player = Player.objects.get(sid=sid)
    context['player'] = player
    if request.method == 'POST':
        post = request.POST
        print(post)
        player.message = validation(
            post['message'][:50]) if 'message' in post else player.message
        player.twitter = post.get('twitter', player.twitter)
        player.twitch = post.get('twitch', player.twitch)
        player.booth = post.get('booth', player.booth)
        if 'rival' in post:
            rival_sid = post['rival']
            rival = Player.objects.get(sid=rival_sid)
            user.player.rival = rival
            user.player.save()
            return redirect('app:rivalpage')
        if 'icon_scoresaber' in post:
            url = f'https://scoresaber.com/api/player/{player.sid}/basic'
            res = requests.get(url).json()
            imageURL = res['profilePicture']
            player.imageURL = imageURL
        if 'icon_discord' in post:
            if social.extra_data['avatar'] != None:
                player.imageURL = f'https://cdn.discordapp.com/avatars/{social.uid}/{social.extra_data["avatar"]}'
        player.userColor = post.get('color', player.userColor)
        player.bgColor = post.get('bg', player.bgColor)
        player.isShadow = 'shadow' in post

        if 'mapper' in post:
            process_mapper(post, player, context)

        player.save()

    eyebeam_count = Player.objects.filter(rival=player).count()
    top10_scores = Score.objects.filter(
        player=player, league__name='Top10').order_by('-rawPP')
    player_badges = Badge.objects.filter(player=player)

    context.update({
        'eyebeam': eyebeam_count,
        'top10': top10_scores,
        'badges': player_badges,
    })

    players = Player.objects.aggregate(
        Max('accPP'), Max('techPP'), Max('passPP')
    )
    accMax = players['accPP__max']
    techMax = players['techPP__max']
    passMax = players['passPP__max']

    accIndex = player.accPP/accMax*100 if accMax > 0 else 0
    techIndex = player.techPP/techMax*100 if techMax > 0 else 0
    passIndex = player.passPP/passMax*100 if passMax > 0 else 0

    context.update({
        'acc': accIndex,
        'tech': techIndex,
        'pass': passIndex
    })

    max_color = max(accIndex, techIndex, passIndex)

    if max_color == 0:
        pass_col = 0
        acc_col = 0
        tech_col = 0
    else:
        pass_col = int(passIndex*255/max_color)
        acc_col = int((accIndex/max_color) ** 3 * 255)
        tech_col = int(techIndex*255/max_color)

    context['style_color'] = f'rgba({pass_col},{acc_col},{tech_col},.8)'

    def get_player_type(tech_index, acc_index, pass_index):
        player_type = 'バランス型'

        comparisons = [
            (tech_index, acc_index, pass_index, 'テック型', 'かなりテック型'),
            (acc_index, tech_index, pass_index, '精度型', 'かなり精度型'),
            (pass_index, acc_index, tech_index, 'クリアラー型', 'かなりクリアラー型'),
        ]

        for index, other_index1, other_index2, label, strong_label in comparisons:
            if index > other_index1 * 1.2 and index > other_index2 * 1.2:
                player_type = strong_label
            elif index > other_index1 * 1.1 and index > other_index2 * 1.1:
                player_type = label

        return player_type

    context['player_type'] = get_player_type(techIndex, accIndex, passIndex)

    return render(request, 'userpage.html', context)


@login_required
def mypage(request):
    user = request.user
    social = SocialAccount.objects.get(user=user)
    context = {}
    context['social'] = social
    # player registartion
    if not Player.objects.filter(user=user).exists():
        player = Player.objects.create(user=user)
        player.discordID = social.uid
        player.save()
    # registration end
    if not user.player.isActivated:
        return render(request, 'activation.html', context)
    player = user.player
    return redirect('app:userpage', sid=player.sid)


def create_song_by_hash(hash, diff_num, char, lid):
    if lid == None:
        return None
    if Song.objects.filter(lid=lid).exists():
        return Song.objects.get(lid=lid)
    url = f'https://api.beatsaver.com/maps/hash/{hash}'
    res = requests.get(url).json()
    if 'error' in res:
        print('error! in create_song_by_hash')
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


def create_headline(player, title, diff, old_acc=None, new_acc=None):
    if old_acc is not None:
        text = f'{player} さんが {title} ({diff}) のスコアを更新！ {old_acc:.2f} -> {new_acc:.2f} %'
    else:
        text = f'{player} さんが {title} ({diff}) のスコアを更新！ {new_acc:.2f} %'

    return Headline.objects.create(
        player=player,
        time=django_timezone.now(),
        text=text,
    )


def score_to_headline(new_score, song, player, league):
    title = song.title[:30] + '...' if len(song.title) > 30 else song.title
    new_acc = score_to_acc(new_score, song.notes)

    old_score = Score.objects.filter(
        player=player, song=song, league=league).first()

    if old_score is not None:
        if new_score > old_score.score:
            old_acc = old_score.acc
            return create_headline(player, title, song.diff, old_acc, new_acc)
    else:
        return create_headline(player, title, song.diff, None, new_acc)


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
    league = League.objects.get(name='Top10')

    # inititalize
    initialize = False # 普段は False だけど、ナーフがあった時だけ True にして Push
    # initialize = True
    if initialize:
        for score in Score.objects.filter(player=player, league__name='Top10').order_by('-rawPP'):
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
        # print(defaults)
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

    # beatleader hmd
    url = f'https://api.beatleader.xyz/player/{player.sid}?stats=true'
    res = requests.get(url)
    if res.status_code == 200:
        res = res.json()
        if res['scoreStats']['topHMD'] in hmd_dict:
            hmd = hmd_dict[res['scoreStats']['topHMD']]
            if hmd != 'Unknown':
                player.hmd = hmd

    player.save()
    return


@login_required
def activate_process(request):
    user = request.user
    player = user.player
    if player.isActivated:
        return redirect('app:mypage')
    context = {}
    social = SocialAccount.objects.get(user=user)
    context['social'] = social
    if request.method == 'POST':
        url = request.POST.get('url')
        print(url)
        sid = url.split('/')[-1]
        print(sid)
        # basic information
        url = f'https://scoresaber.com/api/player/{sid}/basic'
        res = requests.get(url).json()
        if res['country'] != 'JP':
            context['error'] = '日本人以外のプレイヤーは登録できません。Sorry, Only Japanese player can be registered.'
            return render(request, 'activation.html', context)
        if Player.objects.filter(sid=sid).exists():
            context['error'] = 'すでにこのスコアセイバーIDで登録しているユーザーがいます。もし、自分のアカウントを他のユーザーによって使われている場合、管理者（hibit）までご連絡ください。'
            return render(request, 'activation.html', context)
        name = res['name']
        imageURL = res['profilePicture']
        pp = res['pp']
        player.name = name
        player.sid = sid
        player.imageURL = imageURL
        player.isActivated = True
        player.pp = pp
        player.save()
        text = f'{player} さんが参加しました！　JBSL-Webへようこそ！'
        Headline.objects.create(
            player=player,
            text=text,
            time=datetime.now()
        )
        # top score registration
        top_score_registration(player)
        return redirect('app:mypage')
    return render(request, 'activation.html', context)


def search_lid(hash, gameMode, diff_num):
    url = f'https://scoresaber.com/api/leaderboard/get-difficulties/{hash}'
    res = requests.get(url).json()
    if 'errorMessage' in res:
        return None
    for r in res:
        if r['difficulty'] != diff_num:
            continue
        if r['gameMode'] != gameMode:
            continue
        return r['leaderboardId']
    return None


def add_playlist(playlist, json_data):
    for song in json_data['songs']:
        hash = str(song['hash']).upper()
        print('searched song is', song)
        difficulty = None
        gameMode = None
        char = None
        if 'difficulties' not in song:
            url = f'https://api.beatsaver.com/maps/hash/{hash}'
            res = requests.get(url).json()
            version = res['versions'][0]
            dif_idx = -1
            difficulty = version['diffs'][dif_idx]
            while difficulty['characteristic'] == 'Lightshow':
                dif_idx -= 1
                difficulty = version['diffs'][dif_idx]
            diff = difficulty['difficulty']
            char = difficulty['characteristic']
            gameMode = char_dict_inv[char]
        else:
            difficulty = song['difficulties'][0]
            char = difficulty['characteristic']
            gameMode = char_dict_inv[char]
            diff = difficulty['name']
            diff = diff[0].upper() + diff[1:]
        print(diff)
        if not Song.objects.filter(hash=hash, diff=diff, char=char).exists():
            print('song does not exist so create')
            diff_num = diff_label_inv[diff]
            print(diff_num)
            if search_lid(hash, gameMode, diff_num) == None:
                print('no LID')

                # try beatleader

                # beatleader id list-up
                url = f'https://api.beatleader.xyz/leaderboards/hash/{hash}'
                res = requests.get(url).json()
                bid = -1
                for r in res['leaderboards']:
                    # print(r['id'])
                    bid = r['id']
                    res_diff = r['difficulty']['difficultyName']
                    res_mode = r['difficulty']['modeName']
                    print(res_diff, res_mode)
                    if res_diff == diff and res_mode == char:
                        break
                beatleader_song = create_song_by_beatleader(
                    hash, char, diff, bid)
                if beatleader_song != None:
                    print('add by beatleader', beatleader_song)
                    playlist.songs.add(beatleader_song)

                continue
            lid = search_lid(hash, gameMode, diff_num)
            print(lid)
            create_song_by_hash(hash, diff_num, char, lid)

        # 作成に失敗した場合は強制終了、基本的には発生しない
        print(hash, diff, char)
        if not Song.objects.filter(hash=hash, diff=diff, char=char).exists():
            print('failed!')
            continue

        song_object = Song.objects.get(hash=hash, diff=diff, char=char)
        print('add by scoresaber', song_object)
        playlist.songs.add(song_object)
        print(hash, char, diff)


@login_required
def create_playlist(request):
    context = {}
    user = request.user
    social = SocialAccount.objects.get(user=user)
    context['social'] = social
    if request.method == 'POST':
        post = request.POST
        print(post)
        if 'playlist' in post and post['playlist'] == '':
            context['error'] = 'ERROR : プレイリストファイルが存在しません。'
            return render(request, 'create_playlist.html', context)
        if 'playlist' in request.FILES:
            json_data = json.load(request.FILES['playlist'].file)
            title = json_data['playlistTitle']
            image = str(json_data['image'])
            if not image.startswith('data:'):
                image = 'data:image/png;base64,' + image
            description = ''
            if 'playlistDescription' in json_data:
                description = json_data['playlistDescription'][:200]
            editor = request.user.player
            isEditable = False
            if 'editable' in request.POST:
                isEditable = True
            if Playlist.objects.filter(title=title).exists():
                context['error'] = 'ERROR : すでに同名のプレイリストが存在します。'
                return render(request, 'create_playlist.html', context)
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
            return redirect('app:playlists', 1)
        if 'title' in post:
            title = post['title']
            description = post['description']
            if Playlist.objects.filter(title=title).exists():
                context['error'] = 'ERROR : すでに同名のプレイリストが存在します。'
                return render(request, 'create_playlist.html', context)
            isHidden = True
            if 'open' in request.POST:
                isHidden = False                
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
                isHidden=isHidden,
                image='data:image/png;base64,' + img_str
            )
            return redirect('app:playlist', pk=playlist.pk)

    return render(request, 'create_playlist.html', context)


def playlists(request, page=1):
    context = {}
    user = request.user
    if user.is_authenticated:
        social = SocialAccount.objects.get(user=user)
        context['social'] = social
    start = 8*(page-1)
    end = 8*page
    limit = (Playlist.objects.all().count() + 7) // 8
    print(limit)

    from django.db.models import Q

    if user.is_authenticated:
        playlists = Playlist.objects.all().order_by('-pk').filter(
            Q(isHidden=False) | Q(editor=user.player) | Q(CoEditor=user.player)).distinct()[start:end]
    else:
        playlists = Playlist.objects.all().order_by(
            '-pk').filter(isHidden=False)[start:end]
    archives = Playlist.objects.all().order_by(
        '-pk').filter(isHidden=False)[start:end]
    # playlists = make_sorted_playlists(playlists)
    weekly = Playlist.objects.get(title='JP Weekly')
    biweekly = Playlist.objects.get(title='JP Biweekly')
    latest = Playlist.objects.get(title='JP Latest')
    context['weekly'] = weekly
    context['biweekly'] = biweekly
    context['latest'] = latest
    context['playlists'] = playlists
    context['archives'] = archives
    context['page'] = page
    context['limit'] = limit
    return render(request, 'playlists.html', context)


def make_sorted_playlist(playlist: Playlist):
    from operator import attrgetter
    sorted_songs = []

    for song in playlist.songs.all():
        songinfo, created = SongInfo.objects.get_or_create(
            song=song, playlist=playlist)
        song.order = songinfo.order if not created else 0
        song.genre = songinfo.genre if not created else None
        sorted_songs.append(song)

    sorted_songs = sorted(sorted_songs, key=attrgetter('order'))
    playlist.sorted_songs = sorted_songs

    return playlist


def create_song_by_beatleader(hash, char, dif, bid):
    if Song.objects.filter(bid=bid).exists():
        return Song.objects.get(bid=bid)
    url = f'https://api.beatleader.xyz/leaderboard/{bid}'
    res = requests.get(url)
    if res.status_code != 200:
        return None
    res = res.json()
    bsr = res['song']['id']
    title = res['song']['name']
    author = res['song']['mapper']
    notes = res['difficulty']['notes']
    imageURL = res['song']['coverImage']
    color = col_dict[res['difficulty']['value']]
    print(bsr, title, author, dif, notes, color)
    return Song.objects.create(
        title=title,
        author=author,
        diff=dif,
        char=char,
        notes=notes,
        bsr=bsr,
        hash=hash,
        lid=None,
        color=color,
        imageURL=imageURL,
        bid=bid,
    )


def playlist(request, pk):
    context = {}
    user = request.user
    playlist = Playlist.objects.get(pk=pk)

    # hidden kick
    if playlist.isHidden:
        if not user.is_authenticated:
            return redirect('app:index')
        else:
            print(playlist.CoEditor.all())
            if not (playlist.editor == user.player or user.player in playlist.CoEditor.all()):
                return redirect('app:index')

    # leagues
    leagues = League.objects.filter(playlist=playlist)
    print(leagues)
    context['leagues'] = leagues

    # reorder
    if user.is_authenticated:
        if playlist.editor == user.player:
            playlist = make_sorted_playlist(playlist)
            for i, song in enumerate(playlist.sorted_songs):
                print(song)
                songInfo = SongInfo.objects.get(song=song, playlist=playlist)
                songInfo.order = i
                songInfo.save()

    # coeditor
    coeditors = playlist.CoEditor.all()
    context['coeditors'] = coeditors
    context['playlist'] = playlist

    # league_used check
    league_used = League.objects.filter(playlist=playlist).exists()
    context['league_used'] = league_used

    if user.is_authenticated:
        social = SocialAccount.objects.get(user=user)
        context['social'] = social
        isEditor = user.player == playlist.editor or user.player in playlist.CoEditor.all()
        context['isEditor'] = isEditor

    if request.method == 'POST':
        post = request.POST
        files = request.FILES
        print(post)
        print(files)
        if 'add_song' in post and post['add_song'] != '':
            lid = post['add_song'].split('/')[-1]
            url = f'https://scoresaber.com/api/leaderboard/by-id/{lid}/info'
            res = requests.get(url).json()
            if True: # BeatLeader の方をデフォにするため
                bsr = lid
                url = f'https://api.beatsaver.com/maps/id/{bsr}'
                res = requests.get(url)
                if res.status_code == 200:
                    res = res.json()
                    print(res)
                    name = res['name']  
                    author = res['uploader']['name']
                    hash = res['versions'][0]['hash']
                    context['hash'] = hash
                    context['name'] = name
                    context['author'] = author
                    data = res['versions'][0]['diffs']
                    context['data'] = data
                    if post['sort_index'] != '':
                        context['sort_index'] = int(post['sort_index'])
                    return render(request, 'add_diff_by_map.html', context)
                context['errorMessage'] = 'URL の解析に失敗しました。'
                print('error')
                return render(request, 'playlist.html', context)
            hash = res['songHash']
            diff_num = res['difficulty']['difficulty']
            gameMode = res['difficulty']['gameMode']
            char = char_dict[gameMode]
            song = create_song_by_hash(hash, diff_num, char, lid)
            sort_index = playlist.songs.all().count()
            if post['sort_index'] != '':
                sort_index = float(post['sort_index'])
            if song is not None:
                playlist.songs.add(song)
                # if not SongInfo.objects.filter(song=song,playlist=playlist).exists():
                SongInfo.objects.update_or_create(
                    song=song,
                    playlist=playlist,
                    defaults={'order': sort_index},
                )
            return redirect('app:playlist', pk=pk)
        if 'remove_song' in post and post['remove_song'] != '':
            song_pk = post['remove_song']
            song = Song.objects.get(pk=song_pk)
            playlist.songs.remove(song)
            return redirect('app:playlist', pk=pk)
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
                return redirect('app:playlists', 1)
        if 'editable' in post:
            playlist.isEditable = not playlist.isEditable
            playlist.save()
        if 'title' in post and post['title'] != '':
            title = post['title']
            print(title)
            playlist.title = title
            playlist.save()
        if 'up' in post:
            # lid = post['up']
            song_pk = post['up']
            song = Song.objects.get(pk=song_pk)
            songInfo = SongInfo.objects.get(song=song, playlist=playlist)
            songInfo.order -= 1
            songInfo.save()
            # swap
            for swapped_song in SongInfo.objects.filter(playlist=playlist, order=songInfo.order):
                print(swapped_song)
                swapped_song.order += 1
                swapped_song.save()
            songInfo.save()
            return redirect('app:playlist', pk=pk)
        if 'down' in post:
            # lid = post['down']
            song_pk = post['down']
            song = Song.objects.get(pk=song_pk)
            songInfo = SongInfo.objects.get(song=song, playlist=playlist)
            songInfo.order += 1
            # swap
            for swapped_song in SongInfo.objects.filter(playlist=playlist, order=songInfo.order):
                print(swapped_song)
                swapped_song.order -= 1
                swapped_song.save()
            songInfo.save()
            return redirect('app:playlist', pk=pk)
        if 'add_from_map' in post:
            hash = post['hash']
            char = post['char']
            dif = post['dif']
            gameMode = char_dict_inv[char]
            diff_num = diff_label_inv[dif]
            print(hash, char, dif)
            lid = search_lid(hash, gameMode, diff_num)
            sort_index = playlist.songs.all().count()
            if post['sort_index'] != '':
                sort_index = float(post['sort_index'])
            print(sort_index)
            if lid == None:
                print('no lid')
                context['errorMessage'] = 'スコアセイバーの ID が見つかりません'

                # beta v3 registartion

                # beatleader id list-up
                url = f'https://api.beatleader.xyz/leaderboards/hash/{hash}'
                res = requests.get(url).json()
                print(res)
                bid = -1
                for r in res['leaderboards']:
                    # print(r['id'])
                    bid = r['id']
                    res_diff = r['difficulty']['difficultyName']
                    res_mode = r['difficulty']['modeName']
                    print(res_diff, res_mode)
                    print(dif, char)
                    if res_diff == dif and res_mode == char:
                        break
                if bid == -1:
                    context['errorMessage'] = 'ビートリーダーの ID 検出が正常に起動しませんでした'
                print(bid)
                song = create_song_by_beatleader(hash, char, dif, bid)
                if song is not None:
                    playlist.songs.add(song)
                    SongInfo.objects.update_or_create(
                        song=song,
                        playlist=playlist,
                        defaults={'order': sort_index},
                    )
                return redirect('app:playlist', pk=pk)
            else:
                print(lid)
                song = create_song_by_hash(hash, diff_num, char, lid)
                if song is not None:
                    playlist.songs.add(song)
                    SongInfo.objects.update_or_create(
                        song=song,
                        playlist=playlist,
                        defaults={'order': sort_index},
                    )
                    # playlist.recommend.remove(song)
                return redirect('app:playlist', pk=pk)
        if 'genre' in post:
            genre = post['genre']
            song_pk = post['song_id']
            # print(genre,pk)
            song_info = SongInfo.objects.get(
                song__pk=song_pk, playlist=playlist)
            if genre != "---":
                song_info.genre = genre
            else:
                song_info.genre = None
            song_info.save()
            # print(song_info)
            return redirect('app:playlist', pk=pk)
        if 'back_hidden' in post:
            playlist.isHidden = True
            playlist.save()
            return redirect('app:playlist', pk=pk)
        if 'to_open' in post:
            playlist.isHidden = False
            playlist.save()
            return redirect('app:playlist', pk=pk)

    playlist = make_sorted_playlist(playlist)
    context['playlist'] = playlist

    # genre
    genres = [
        "---",
        "Acc",
        "Tech",
        "Balanced",
        "FullRange",
        "Speed",
        "Stamina",
        "Concept",
    ]
    context['genres'] = genres

    return render(request, 'playlist.html', context)


def download_playlist(request, pk):
    playlist = Playlist.objects.get(pk=pk)
    playlist = make_sorted_playlist(playlist)

    download_url = reverse('app:download_playlist', args=[pk])
    meta_url = request._current_scheme_host

    json_data = {
        'playlistTitle': playlist.title,
        'playlistAuthor': 'JBSL_Web_System',
        'playlistDescription': playlist.description,
        'customData': {'syncURL': meta_url + download_url},
        'image': playlist.image,
        'songs': [
            {
                'songName': song.title,
                'levelAuthorName': song.author,
                'hash': song.hash,
                'difficulties': [
                    {
                        'characteristic': song.char,
                        'name': song.diff
                    }
                ]
            }
            for song in playlist.sorted_songs
        ]
    }

    download_data = json.dumps(json_data, ensure_ascii=False)
    return HttpResponse(download_data)


def leagues(request):
    user = request.user
    social = user.socialaccount_set.first() if user.is_authenticated else None

    active_leagues = League.objects.filter(
        isOpen=True, isLive=True).order_by('-isOfficial', 'end', '-pk')
    end_leagues = League.objects.filter(
        isOpen=True, isLive=False).order_by('-end', '-pk')

    context = {
        'social': social,
        'active_leagues': active_leagues,
        'end_leagues': end_leagues,
    }

    return render(request, 'leagues.html', context)


def calculate_scoredrank_LBs(league, virtual=None, record=False):
    # リーグ内プレイヤーの人数
    base = league.player.count() + 3
    # リーグ内マップ
    playlist = league.playlist
    playlist = make_sorted_playlist(playlist)
    songs = league.playlist.sorted_songs
    # プレイヤーごとのスコア
    total_rank = defaultdict(list)
    # マップごとのプレイヤーランキング
    for song in songs:
        query = Score.objects.filter(
            song=song, league=league).filter(Q(player__league=league) | Q(player=virtual)).order_by('-score').distinct()

        for rank, score in enumerate(query):
            pos = base + slope(rank + 1)
            setattr(score, 'rank', rank+1)
            setattr(score, 'pos', pos)

            # 精度により点数を強調
            decorate = get_decorate(score.acc)
            setattr(score, 'decorate', decorate)

            player = score.player
            total_rank[player].append(score)
        setattr(song, 'scores', query)
    # 順位点→精度でソート

    for player in total_rank:
        total_rank[player] = sorted(
            total_rank[player], key=lambda x: (-x.pos, -x.acc))
    # 有効範囲の分だけ合算する
    players = []
    count_range = league.max_valid
    for player, score_list in total_rank.items():
        score_list = score_list[:count_range]
        for score in score_list:
            setattr(score, 'valid', 1)
        valid_count = len(score_list)
        max_pos = league.max_valid * (base + slope(1))
        count_pos = sum([s.pos for s in score_list])
        theoretical = count_pos / max_pos * 100
        count_acc = sum([s.acc for s in score_list])/valid_count

        # 精度により点数を強調
        decorate = get_decorate(count_acc)
        setattr(player, 'decorate', decorate)

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
        if Participant.objects.filter(league=league, player=player).exists():
            comment = Participant.objects.get(
                league=league, player=player).message
            setattr(player, 'comment', comment)
        players.append(player)
    # 順位点→精度でソート
    players = sorted(
        players, key=lambda x: (-x.count_pos, -x.count_acc))
    for rank, player in enumerate(players):
        setattr(player, 'rank', rank+1)
    return players, songs


def check_membership_and_ownership(user, league):
    is_member = False
    is_owner = False
    if user.is_authenticated:
        if user.player in league.player.all():
            is_member = True
        if user.player == league.owner:
            is_owner = True
    return is_member, is_owner


def get_join_state(user: User, is_member, league: League, player: Player, is_close, is_prohibited):
    join_state = -1
    if user.is_authenticated:
        if is_member:
            join_state = 0
        elif not league.isLive:
            join_state = 1
        elif not league.isPublic:
            join_state = 2
        elif player.borderPP > league.limit:
            join_state = 3
        elif is_close:
            join_state = 4
        elif is_prohibited:
            join_state = 5
        else:
            join_state = 6
        print(join_state)
    return join_state


join_comment = {
    -1: '',
    0: 'あなたはこのリーグに参加しています。',
    1: '終了したリーグに参加することはできません。',
    2: '非公開のリーグに参加することはできません。',
    3: 'あなたは実力が高すぎるため、このリーグには参加できません……。',
    4: '公式リーグでは、終了 48 時間前を過ぎると参加することはできません。',
    5: '同時参加不可能なリーグにすでに参加しているため、このリーグには参加できません。',
    6: '',
}


def leaderboard(request, pk):
    context = {}
    user = request.user
    player = None
    if user.is_authenticated:
        social = SocialAccount.objects.get(user=user)
        context['social'] = social
        player = Player.objects.get(user=user)
    league = League.objects.get(pk=pk)
    context['league'] = league

    # prohibited leagues
    is_prohibited = False
    if player:
        user_leagues = player.league.all()
        prohibited_leagues = league.prohibited_leagues.all()
        is_prohibited = any(user_league in prohibited_leagues for user_league in user_leagues)
        print(is_prohibited)
    # 

    duration_start = time()
    scored_rank, LBs = calculate_scoredrank_LBs(league)
    durtaion = time() - duration_start

    context['scored_rank'] = scored_rank
    context['LBs'] = LBs

    is_member, is_owner = check_membership_and_ownership(user, league)

    close_line = league.end - timedelta(days=2)
    is_close = datetime.now(timezone.utc) >= close_line and league.isOfficial
    context['isClose'] = is_close

    join_state = get_join_state(user, is_member, league, player, is_close, is_prohibited)

    context['join_state'] = join_state
    context['join_comment'] = join_comment[join_state]
    context['edit_state'] = is_owner and league.isLive
    context['isOwner'] = is_owner
    context['isMember'] = is_member
    context['twitch_show'] = request.GET.get('twitch_show', 'off')
    context['discord_show'] = request.GET.get('discord_show', 'off')

    end_str = (league.end + timedelta(hours=9)).strftime('%Y-%m-%dT%H:%M')
    close_str = (league.end + timedelta(hours=9-48)).strftime('%Y-%m-%dT%H:%M')
    context['end_str'] = end_str
    context['close_str'] = close_str

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
        if 'remove_song' in post:
            song_pk = post['remove_song']
            playlist = league.playlist
            playlist.songs.remove(Song.objects.get(pk=song_pk))
            return redirect('app:leaderboard', pk=pk)

    not_invite_players = Player.objects.exclude(
        league=league).exclude(invite=league).filter(isActivated=True).order_by('-borderPP')
    context['not_invite_players'] = not_invite_players

    if 'comment' in request.GET:
        context['comment_open'] = 'open'

    load_index = league.player.all().count() * league.playlist.songs.all().count()
    context['load_index'] = load_index
    context['duration'] = durtaion * 1000

    return render(request, 'leaderboard.html', context)


@login_required
def create_league(request):
    get = request.GET
    context = {}
    if 'pk' in get:
        print(get['pk'])
        context['select'] = int(get['pk'])
        if Playlist.objects.filter(pk=int(get['pk'])).exists():
            selected_playlist = Playlist.objects.get(pk=int(get['pk']))
            context['selected_playlist'] = selected_playlist
        print(type(context['select']))
    user = request.user
    social = SocialAccount.objects.get(user=user)
    context['social'] = social
    default_end = datetime.now() + timedelta(days=14)
    default_end_str = default_end.strftime('%Y-%m-%dT%H:%M')
    context['default_end_str'] = default_end_str
    playlists = Playlist.objects.all().filter(editor=user.player).order_by('-pk')
    playlists = playlists.annotate(num_of_songs=Count('songs'))
    if not user.is_staff:
        playlists = playlists.filter(num_of_songs__lte=20)
    playlists = playlists.filter(isHidden=False)[:20]
    context['playlists'] = playlists
    context['league_colors'] = league_colors
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
            context['error'] = 'プレイリストの曲数が多すぎます。上限は 20 です。'
            return render(request, 'create_league.html', context)
        league = League.objects.create(
            name=title,  # 名称の不一致。余裕があれば後で直す。
            owner=user.player,
            description=description,
            color=color,
            end=end,
            playlist=playlist,
            max_valid=valid,
            isPublic=isPublic,
            isOpen=True,
            limit=limit,
        )
        return redirect('app:leaderboard', pk=league.pk)
    return render(request, 'create_league.html', context)


@login_required
def virtual_league(request, pk):
    context = {}
    user = request.user
    player = user.player
    if user.is_authenticated:
        social = SocialAccount.objects.get(user=user)
        context['social'] = social
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
    context['league'] = league
    scored_rank, LBs = calculate_scoredrank_LBs(league, user.player)
    context['scored_rank'] = scored_rank
    context['LBs'] = LBs

    border_line = league.border_line

    context['border_line'] = border_line

    return render(request, 'virtual_league.html', context)


@login_required
def rivalpage(request):
    context = {}
    user = request.user
    social = SocialAccount.objects.get(user=user)
    context['social'] = social
    player = user.player
    context['player'] = player
    songs = Song.objects.all()
    compares = []
    match = 0
    win = 0

    class compared_score:

        my_acc = 0
        rival_acc = 0

        def __init__(self) -> None:
            pass

        def set_my_acc(self, acc: float):
            self.my_acc = max(self.my_acc, acc)

        def set_rival_acc(self, acc: float):
            self.rival_acc = max(self.rival_acc, acc)

        def win(self) -> bool:
            return self.my_acc >= self.rival_acc

        def dif(self) -> int:
            return self.my_acc - self.rival_acc

        def __repr__(self) -> str:
            return f'{self.my_acc} vs {self.rival_acc}'

    from collections import defaultdict

    d = defaultdict(compared_score)

    for league in League.objects.filter(player=player):
        for score in Score.objects.filter(league=league, player=player):
            song = score.song
            d[song].set_my_acc(score.acc)

    for league in League.objects.filter(player=player.rival):
        for score in Score.objects.filter(league=league, player=player.rival):
            song = score.song
            d[song].set_rival_acc(score.acc)

    for key, val in d.items():
        if val.my_acc > 0 and val.rival_acc > 0:
            match += 1
            compares.append({
                'song': key,
                'your_acc': val.my_acc,
                'rival_acc': val.rival_acc,
                'win': val.win(),
                'dif': val.dif(),
            })
            win += val.win()

    compares = sorted(compares, key=lambda x: -x['dif'])
    context['compares'] = compares
    context['match'] = match
    context['win'] = win
    context['lose'] = match - win

    # POST

    if request.method == 'POST':
        post = request.POST
        print(post)
        if 'no_rival' in post:
            user.player.rival = None
            user.player.save()
            return redirect('app:mypage')
    return render(request, 'rivalpage.html', context)


def headlines(request, page=1):
    context = {}
    user = request.user
    if user.is_authenticated:
        social = SocialAccount.objects.get(user=user)
        context['social'] = social
    start = (page-1) * 100
    end = page * 100
    headlines = Headline.objects.all().order_by('-time')[start:end]
    context['headlines'] = headlines
    context['page'] = page
    context['limit'] = (Headline.objects.all().count() + 99)//100
    return render(request, 'headlines.html', context)


def players(request, sort='borderPP', page=1):
    context = {}
    user = request.user
    page = request.GET.get('page', 1)
    print(page)
    print(request.GET)
    if 'sort' in request.GET:
        sort = request.GET['sort']
    if user.is_authenticated:
        social = SocialAccount.objects.get(user=user)
        context['social'] = social
        player = user.player
        if player.isActivated:
            invitations = player.invite.all()
            context['invitations'] = invitations
    active_players = Player.objects.filter(
        isActivated=True).order_by(f'-{sort}', '-borderPP')
    for i, active in enumerate(active_players):
        setattr(active, 'rank', i+1)
    print(active_players)
    # paginator = Paginator(active_players, 50)
    # players = paginator.get_page(page)

    label = {
        'borderPP': '有効PP',
        'yurufuwa': 'YP',
        'techPP': 'TechPP',
        'passPP': 'PassPP',
    }

    context['active_players'] = active_players
    context['sort'] = sort
    context['label'] = label[sort]
    print(context)
    return render(request, 'players.html', context)


def debug(request):
    if not request.user.is_staff:
        return redirect('app:index')
    active_players = Player.objects.filter(isActivated=True).order_by('-pp')
    context = {}
    context['active_players'] = active_players
    for player in active_players:
        check = defaultdict(int)
        # print(player)
        rivals = []
        if player.rival == None:
            continue
        rival = player
        while True:
            check[rival] += 1
            if check[rival] > 1:
                rivals.append(rival)
                break
            # print('...', rival)
            rivals.append(rival)
            if rival.rival == None:
                break
            rival = rival.rival
        setattr(player, 'rivals', rivals[1:])

    return render(request, 'debug.html', context)


def api_leaderboard(request, pk):
    context = {}
    league = League.objects.get(pk=pk)
    context['league'] = league
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
            'acc': rank.count_acc,
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
    context = {}
    context['twitch'] = ''
    user = request.user
    if user.is_authenticated:
        social = SocialAccount.objects.get(user=user)
        context['social'] = social

    user_state = 0
    if user.is_authenticated:
        player = Player.objects.get(user=user)
        if player.twitch != '':
            user_state = 1

    context['user_state'] = user_state

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
            context['results'] = results
            return render(request, 'bsr_checker.html', context)
        player = Player.objects.get(twitch=twitchID)
        results.append(
            f'マッチするプレイヤー：{player.name}', f'https://jbsl-web.herokuapp.com/userpage/{player.sid}')
        results.append(f'Score Saber : {player.sid}',
                       f'https://scoresaber.com/u/{player.sid}')
        context['results'] = results
        bsr = post['bsr_command'].split(' ')[-1].split('/')[-1]
        results.append(f'検出された bsr key : {bsr}',f'!bsr {bsr}')
        url = f'https://api.beatsaver.com/maps/id/{bsr}'
        res = requests.get(url).json()
        print(res)
        if not 'versions' in res:
            results.append(f'! bsr key から正しい譜面情報を取得できませんでした。')
            context['results'] = results
            return render(request, 'bsr_checker.html', context)
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
        context['twitch'] = twitchURL
        context['results'] = results.results
        context['bsr'] = bsr

    return render(request, 'bsr_checker.html', context)


def info_test(request, pk):
    print(pk)
    context = {}
    user = request.user
    if user.is_authenticated:
        social = SocialAccount.objects.get(user=user)
        context['social'] = social
    return render(request, f'info/info{pk}.html', context)


@login_required
def score_comment(request):
    user = request.user
    social = SocialAccount.objects.get(user=user)
    context = {}
    context['social'] = social
    print(request.method)
    if request.method == "POST":
        post = request.POST
        print(post)
        score = Score.objects.get(pk=post['score'])
        if 'comment' in post:
            score.comment = validation(post['comment'])
            score.save()
            redirect_url = reverse('app:leaderboard', args=[score.league.pk])
            print(redirect_url)
            return redirect(f'{redirect_url}#{score.song.lid}')
        print(score)
        context['score'] = score
        return render(request, 'score_comment.html', context)
    return redirect('app:index')


@login_required
def league_comment(request):
    user = request.user
    social = SocialAccount.objects.get(user=user)
    context = {}
    context['social'] = social
    print(request.method)
    print('league comment')
    if request.method == "POST":
        post = request.POST
        print(post)
        league = League.objects.get(pk=post['league'])
        player = Player.objects.get(pk=post['player'])
        context['league'] = league
        context['player'] = player
        if 'comment' in post:
            comment = post['comment'][:50]
            defaults = {'message': validation(comment)}
            Participant.objects.update_or_create(
                league=league,
                player=user.player,
                defaults=defaults,
            )
            return redirect('app:leaderboard', pk=league.pk)
        if Participant.objects.filter(league=league, player=player).exists():
            comment = Participant.objects.get(league=league, player=player)
            setattr(player, 'comment', comment)
        return render(request, 'league_comment.html', context)
    return redirect('app:index')


@login_required
def league_edit(request, pk):
    user = request.user
    social = SocialAccount.objects.get(user=user)
    context = {}
    context['social'] = social
    print(request.method)
    print('league edit')
    league = League.objects.get(pk=pk)
    player = Player.objects.get(user=user)
    context['league'] = league
    print(league)
    if league.owner != player:
        return redirect('app:index')
    end_str = (league.end + timedelta(hours=9)).strftime('%Y-%m-%d %H:%M')
    context['end_str'] = end_str
    context['league_colors'] = league_colors

    not_invite_players = Player.objects.exclude(
        league=league).exclude(invite=league).filter(isActivated=True).order_by('-borderPP')
    invite_players = Player.objects.filter(invite=league).order_by('-borderPP')
    context['not_invite_players'] = not_invite_players
    context['invite_players'] = invite_players

    if request.method == 'POST':
        post = request.POST
        print(post)
        if 'title' in post:
            league.name = post['title']
            if post['description'] != '':
                league.description = post['description']
            league.end = datetime.strptime(post['end'], '%Y-%m-%dT%H:%M')
            league.max_valid = post['valid']
            league.limit = post['limit']
            league.color = post['color']
            league.border_line = post['border-line']
            league.isPublic = 'public' in post
            league.save()
            if not 'back' in post:
                return redirect('app:league_edit', pk=pk)
            else:
                return redirect('app:leaderboard', pk=pk)
        if 'invite' in post:
            invites = post.getlist('invite')
            for invite in invites:
                invite_player = Player.objects.get(sid=invite)
                league.invite.add(invite_player)
        if 'withdraw' in post:
            withdraw = Player.objects.get(sid=post['withdraw'])
            print(withdraw)
            league.invite.remove(withdraw)
            redirect('app:league_edit', pk=pk)
    return render(request, 'league_edit.html', context)


def playlist_archives(request):
    context = {}
    user = request.user
    if user.is_authenticated:
        social = SocialAccount.objects.get(user=user)
        context['social'] = social
    archives = Playlist.objects.all().order_by('-pk').exclude(isHidden=True)
    cnt = 0
    for archive in archives:
        print(archive)
        setattr(archive, 'page', cnt//8 + 1)
        cnt += 1
    context['archives'] = archives
    return render(request, 'playlist_archives.html', context)


def owner_comment(request):
    user = request.user
    social = SocialAccount.objects.get(user=user)
    context = {}
    context['social'] = social
    print(request.method)
    print('owner comment')
    if request.method == "POST":
        post = request.POST
        print(post)
        league = League.objects.get(pk=post['league'])
        if user.player != league.owner:
            return redirect('app:index')
        context['league'] = league
        print(league)
        if 'owner_comment' in post:
            owner_comment = post['owner_comment'][:1000]
            print(owner_comment)
            league.ownerComment = owner_comment
            league.save()
        if 'back' in post:
            url = reverse('app:leaderboard', args=[league.pk])
            print(url)
            url += '?comment=open'
            return redirect(url)
        return render(request, 'owner_comment.html', context)
    return redirect('app:index')


@login_required
def badge_adding(request, sid, badge_name):
    if not request.user.is_staff:
        return redirect('app:index')
    badge_name = badge_name.replace('_', ' ')
    badge = Badge.objects.get(name=badge_name)
    player = Player.objects.get(sid=sid)
    badge.player = player
    badge.save()
    print(badge, player)
    return redirect('app:index')


def pos_acc_update(pk):
    league = League.objects.get(pk=pk)
    print(league)
    # リーグ内プレイヤーの人数
    base = league.player.count() + 3
    # リーグ内マップ
    playlist = league.playlist
    songs = playlist.songs.all()
    # マップごとのプレイヤーランキング
    for song in songs:
        print(song)
        query = Score.objects.filter(
            song=song, league=league, player__league=league).order_by('-score')
        max_score = -1
        if len(query) > 0:
            max_score = query[0].score
        for rank, score in enumerate(query):
            pos = base + slope(rank + 1)
            score.rank = rank+1
            score.pos = pos
            score.weight_acc = score.score/max_score*100

            print(score.weight_acc)

            decorate = get_decorate(score.acc)
            score.decorate = get_decorate(score.acc)

            score.save()

    players = Player.objects.filter(league=league)
    count_range = league.max_valid

    for player in players:
        participant = None
        if Participant.objects.filter(league=league, player=player).exists():
            participant = Participant.objects.get(league=league, player=player)
        else:
            participant = Participant.objects.create(
                league=league, player=player)
        print(participant)
        query = Score.objects.filter(
            league=league, player=player).order_by('-pos', '-acc')
        for i, score in enumerate(query):
            score.valid = (i < count_range)
            score.save()
        score_list = query[:count_range]
        valid_count = len(score_list)
        max_pos = league.max_valid * (base + slope(1))
        count_pos = sum([s.pos for s in score_list])
        count_weight_acc = sum([s.weight_acc for s in score_list])
        theoretical = count_pos / max_pos * 100
        count_acc = 0
        if valid_count > 0:
            count_acc = sum([s.acc for s in score_list])/valid_count

        decorate = get_decorate(count_acc)
        participant.decorate = decorate

        tooltip_pos = '<br>'.join(
            [f'{score.song.title[:25]}... ({score.pos})' for score in score_list])
        tooltip_weight_acc = '<br>'.join(
            [f'{score.song.title[:25]}...({score.weight_acc:.2f})' for score in score_list])
        tooltip_valid = '<br>'.join(
            [f'{score.song.title[:25]}...' for score in score_list])
        tooltip_acc = '<br>'.join(
            [f'{score.song.title[:25]}... ({score.acc:.2f})' for score in score_list])
        participant.count_pos = count_pos
        participant.count_weight_acc = count_weight_acc
        participant.theoretical = theoretical
        participant.count_acc = count_acc
        participant.valid_count = valid_count
        participant.tooltip_pos = tooltip_pos
        participant.tooltip_valid = tooltip_valid
        participant.tooltip_acc = tooltip_acc
        participant.tooltip_weight_acc = tooltip_weight_acc
        participant.save()

    # 順位点→精度でソート
    participants = Participant.objects.filter(
        league=league).order_by('-count_pos')

    for rank, participant in enumerate(participants):
        # setattr(player, 'rank', rank+1)
        participant.rank = rank+1
        participant.save()


def manual_league_update(request, pk=0):
    if not request.user.is_staff:
        return redirect('app:index')
    pos_acc_update(pk)
    print('complete')
    return redirect('app:index')


def short_leaderboard(request, pk=0):
    from time import time

    duration_start = time()
    context = {}
    user = request.user
    if user.is_authenticated:
        social = SocialAccount.objects.get(user=user)
        context['social'] = social
    league = League.objects.get(pk=pk)
    context['league'] = league
    songs = league.playlist.songs.all()
    context['songs'] = songs

    for song in songs:
        query = Score.objects.filter(
            song=song, league=league, player__league=league).order_by('-score').first()
        setattr(song, 'scores', query)

        if user.is_authenticated:
            if Score.objects.filter(song=song, league=league, player=user.player).exists():
                additional_score = Score.objects.get(
                    song=song, league=league, player=user.player)
                print(additional_score)
                setattr(song, 'additional_score', additional_score)

    context['participants'] = Participant.objects.filter(
        league=league).order_by('-count_pos')
    durtaion = time() - duration_start
    context['duration'] = durtaion * 1000

    return render(request, 'short_leaderboard.html', context)


def song_leaderboard(request, league_pk, song_pk):
    context = {}
    user = request.user
    player = None
    if user.is_authenticated:
        social = SocialAccount.objects.get(user=user)
        context['social'] = social
        player = Player.objects.get(user=user)
    league = League.objects.get(pk=league_pk)
    song = Song.objects.get(lid=song_pk)
    scores = Score.objects.filter(
        song=song, league=league, player__league=league).order_by('-score')
    setattr(song, 'scores', scores)
    context['league'] = league
    context['song'] = song
    return render(request, 'song_leaderboard.html', context)


# @login_required
# def beatleader_submission(request):
#     if request.method != 'POST':
#         return redirect('app:index')
#     player = request.user.player
#     # print(player)
#     post = request.POST
#     # print(post)
#     league_pk = int(post['league_pk'])
#     league = League.objects.get(pk=league_pk)
#     # print(league)
#     playlist = league.playlist
#     songs = playlist.songs.all()
#     context = {}
#     results = []
#     print(songs)
#     for song in songs:
#         updated = False
#         url = f'https://api.beatleader.xyz/score/{player.sid}/{song.hash}/{song.diff}/{song.char}'
#         # print(url)
#         res = requests.get(url)
#         status_code = res.status_code
#         if status_code != 200:
#             continue
#         res = res.json()
#         # print(res)
#         score = int(res['modifiedScore'])
#         print(score)
#         defaults = {
#             'score': score,
#             'acc': float(res['accuracy'])*100,
#             'rawPP': 0,
#             'miss': int(res['missedNotes'] + int(res['badCuts'])),
#             'beatleader': res['id'],
#         }
#         score_to_headline(score, song, player, league)
#         score_obj = Score.objects.update_or_create(
#             player=player,
#             song=song,
#             league=league,
#             defaults=defaults,
#         )[0]
#         result = f'score found {song} {score} ({score_obj.acc:.2f}) %'
#         if updated:
#             result += ' ... UPDATED!'
#         results.append(result)
#     context['league'] = league
#     context['results'] = results
#     return render(request, 'beatleader_submission.html', context)


def archive(request):
    context = {}
    user = request.user
    if user.is_authenticated:
        social = SocialAccount.objects.get(user=user)
        context['social'] = social
    return render(request, 'archive.html', context)


state_dict = {
    -2: 'RETRY PLAYER1 ADVANTAGE',
    -1: 'PLAYER1 WIN SUSPEND',
    0: 'STAND BY',
    1: 'PLAYER2 WIN SUSPEND',
    2: 'RETRY PLAYER2 ADVANTAGE',
}


def match(request, pk=1):

    match = Match.objects.get(pk=pk)
    playlists = Playlist.objects.all().order_by('-pk')
    leagues = League.objects.all().order_by('-pk')
    context = {}
    context['match'] = match
    context['pk'] = pk
    context['isEditor'] = False
    context['playlists'] = playlists
    context['leagues'] = leagues
    user = request.user
    if user.is_authenticated:
        player = Player.objects.get(user=user)
        if player in match.editor.all():
            context['isEditor'] = True

    if request.method == 'POST':
        post = request.POST
        print(post)
        if 'next-song' in post:
            lid = post['next-song']
            song = Song.objects.get(lid=lid)
            match.now_playing = song
            url = f'https://api.beatsaver.com/maps/id/{song.bsr}'
            res = requests.get(url).json()
            bpm = res['metadata']['bpm']
            res = res['versions'][0]['diffs']
            match.map_info = "map info parse failed..."
            for r in res:
                if r['characteristic'] == song.char and r['difficulty'] == song.diff:
                    nps = r['nps']
                    njs = r['njs']
                    notes = int(r['notes'])
                    bombs = r['bombs']
                    match.map_info = f'BPM:{bpm:.1f} NOTES:{notes} BOMBS:{bombs} NPS:{nps:.1f} NJS:{njs:.1f}'
            match.save()
        if 'reset' in post:
            match.result1 = 0
            match.result2 = 0
            match.retry1 = 0
            match.retry2 = 0
            match.state = 0
            match.save()
        if 'player1' in post:
            sid1 = post['player1']
            sid2 = post['player2']
            print(sid1, sid2)
            player1 = Player.objects.get(sid=sid1)
            player2 = Player.objects.get(sid=sid2)
            match.player1 = player1
            match.player2 = player2
            # match.result1 = 0
            # match.result2 = 0
            # match.retry1 = 0
            # match.retry2 = 0
            # match.state = 0
            match.save()
        if 'title' in post:
            title = post['title']
            match.title = title
            match.save()
        if 'playlist' in post:
            pk = post['playlist']
            playlist = Playlist.objects.get(pk=pk)
            match.playlist = playlist
            match.now_playing = playlist.songs.all()[0]
            match.save()
        if 'league' in post:
            pk = post['league']
            league = League.objects.get(pk=pk)
            if league.player.all().count() >= 2:
                print(league)
                match.league = league
                match.player1 = league.player.all()[0]
                match.player2 = league.player.all()[1]
                match.save()

        if 'player1_win' in post:
            if post['highest1'] != '':
                match.highest_acc = float(post['highest1'])
            match.result1 += 1
            match.result2 -= match.result2 % 2  # リトライ状態を戻す、3だったら2に、5だったら4に
            if match.retry2:  # リトライ「を使った後」である時
                match.result1 += 1
                match.result1 -= match.result1 % 2
                match.state = 0
            else:
                match.state = -1
            match.save()
        if 'player2_win' in post:
            if post['highest2'] != '':
                match.highest_acc = float(post['highest2'])
            match.result2 += 1
            match.result1 -= match.result1 % 2
            if match.retry1:
                match.result2 += 1
                match.result2 -= match.result2 % 2
                match.state = 0
            else:
                match.state = 1
            match.save()
        if 'player1_retry' in post:
            match.retry1 = True
            match.state = 2
            match.save()

        if 'player2_retry' in post:
            match.retry2 = True
            match.state = -2
            match.save()

        if 'no_retry' in post:
            if match.state == -1:
                match.result1 += 1
            if match.state == 1:
                match.result2 += 1
            match.state = 0
            match.save()

    context['highest'] = match.highest_acc
    context['state'] = state_dict[match.state]
    context['inMatch'] = match.state % 2 == 0

    return render(request, 'match.html', context)


def api_match(request, pk):
    context = {}
    match = Match.objects.get(pk=pk)
    context['match'] = match
    ans = {}
    ans['title'] = match.title
    ans['player1'] = match.player1.name
    ans['player1-imageURL'] = match.player1.imageURL
    ans['player2'] = match.player2.name
    ans['player2-imageURL'] = match.player2.imageURL
    ans['result1'] = match.result1
    ans['result2'] = match.result2
    ans['retry1'] = match.retry1
    ans['retry2'] = match.retry2
    ans['imageURL'] = match.now_playing.imageURL
    ans['map-info1'] = match.now_playing.title
    ans['map-info2'] = match.now_playing.author
    ans['map-info3'] = match.now_playing.diff
    ans['map-info3-color'] = match.now_playing.color
    ans['map-info4'] = match.map_info
    ans['state'] = match.state
    ans['highest'] = f'{match.highest_acc:.2f}'

    return HttpResponse(json.dumps(ans, indent=4, ensure_ascii=False))


def api_dga(request):
    from .models import DGA
    import json
    dgas = DGA.objects.all()
    if 'sid' in request.GET:
        sid = request.GET['sid']
        dgas = dgas.filter(sid=sid)
    if 'sort' in request.GET:
        key = request.GET['sort']
        dgas = dgas.order_by(key)
    if 'limit' in request.GET:
        limit = int(request.GET['limit'])
        dgas = dgas[:limit]
    post_json = json.dumps(list(dgas.values()), ensure_ascii=False)
    return HttpResponse(post_json, content_type="application/json")


@csrf_exempt
def api_dga_post(request):
    if request.method == 'GET':
        post_json = {
            'message': 'レスポンス 200 で通信成功したと思った？ 残念！ GET じゃこの API は通りません～～～'}
        post_json = json.dumps(post_json, ensure_ascii=False)
        return HttpResponse(post_json, content_type="application/json")
    post = request.POST
    token = post['token']
    auth = ''
    if os.path.exists('local.py'):
        from local import DGA_TOKEN
        auth = DGA_TOKEN
    else:
        auth = os.environ['DGA_TOKEN']
    if token != auth:
        post_json = {'message': 'トークン認証に失敗しました'}
        post_json = json.dumps(post_json, ensure_ascii=False)
        return HttpResponse(post_json, content_type="application/json")
    defaults = {
        'dance': float(post['dance']),
        'gorilla': float(post['gorilla']),
        'song_mapper': post['song_mapper'],
        'player_name': post['player_name'],
        'sid': post['sid'],
    }
    print(defaults)
    dga, check = DGA.objects.update_or_create(
        beatleader=post['beatleader'],
        defaults=defaults
    )
    print(check)
    if not check:
        post_json = {'message': '既にスコアが存在します'}
        post_json = json.dumps(post_json, ensure_ascii=False)
        return HttpResponse(post_json, content_type="application/json")
    post_json = {'message': 'スコアを登録完了しました'}
    post_json = json.dumps(post_json, ensure_ascii=False)
    return HttpResponse(post_json, content_type="application/json")


def player_matrix(request):
    context = {}
    user = request.user
    offset_x = request.GET.get('offset_x', 600)
    offset_y = request.GET.get('offset_y', 600)
    scale = request.GET.get('scale', 1)
    print(offset_x, offset_y)
    if user.is_authenticated:
        social = SocialAccount.objects.get(user=user)
        context['social'] = social
    players = Player.objects.filter(
        isActivated=True, passPP__gt=0, techPP__gt=0)
    from django.db.models import Max, F, ExpressionWrapper, FloatField
    max_pass_pp = players.aggregate(Max('passPP'))['passPP__max']
    max_tech_pp = players.aggregate(Max('techPP'))['techPP__max']

    players = players.annotate(
        relative_passPP=ExpressionWrapper(
            1200 - ((F('passPP') / max_pass_pp * 1000 - offset_y) * scale + 600),
            output_field=FloatField()
        ),
        relative_techPP=ExpressionWrapper(
            200 + (F('techPP') / max_tech_pp * 1000 - offset_x) * scale + 600,
            output_field=FloatField()
        ),
    )

    players = players.filter(
        relative_passPP__gte=200,
        relative_passPP__lte=1200,
        relative_techPP__gte=200,
        relative_techPP__lte=1200,
    )

    players = players.order_by('accPP')
    context['players'] = players
    context['now_offset_x'] = offset_x
    context['now_offset_y'] = offset_y
    context['now_scale'] = scale

    return render(request, 'player_matrix.html', context)


def genre_criteria(request):
    context = {}
    user = request.user
    if user.is_authenticated:
        social = SocialAccount.objects.get(user=user)
        context['social'] = social
    return render(request, f'genre_criteria.html', context)

import base64
import json
import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from io import BytesIO
from time import time

import requests
from PIL import Image
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Max, Prefetch
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from .models import League, Participant, Player, Playlist, Song, Score, Headline, SongInfo, Badge, Match, DGA, User
from .utils import ComparedScore, Results
from .utils import score_to_acc, validation
from .utils import diff_label_inv, char_dict_inv, league_colors, state_dict, genres, join_comment
from .operations import create_song_by_hash, top_score_registration, make_sorted_playlist, calculate_scoredrank_LBs, create_headline, score_to_headline, process_mapper
from .operations import get_headline_and_league_context, search_lid, add_playlist, create_song_by_beatleader, check_membership_and_ownership, get_join_state

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
    return render(request, 'index.html', context)

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
        player=player, league__name='Top10').order_by('-rawPP').prefetch_related('song')
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
    # ユーザー認証状態の確認
    if user.is_authenticated:
        social = SocialAccount.objects.get(user=user)
        context['social'] = social
    # ページネーションの計算
    start = 8 * (page - 1)
    end = 8 * page
    limit = (Playlist.objects.all().count() + 7) // 8
    print(limit)
    from django.db.models import Q
    # プレイリストの基本クエリセット
    playlists = Playlist.objects.prefetch_related('songs').select_related('editor')
    # ユーザーが認証されている場合の処理
    if user.is_authenticated:
        # エディターまたは共同エディターであるか、公開されているプレイリストを選択
        playlists = playlists.order_by('-pk').filter(
            Q(isHidden=False) | Q(editor=user.player) | Q(CoEditor=user.player)
        ).distinct()[start:end]
    # ユーザーが認証されていない場合の処理
    else:
        # 公開されているプレイリストのみを選択
        playlists = playlists.order_by('-pk').filter(isHidden=False)[start:end]
    # 特定のプレイリストを取得
    weekly = Playlist.objects.get(title='JP Weekly')
    biweekly = Playlist.objects.get(title='JP Biweekly')
    latest = Playlist.objects.get(title='JP Latest')
    # コンテキストに情報を追加
    context['weekly'] = weekly
    context['biweekly'] = biweekly
    context['latest'] = latest
    context['playlists'] = playlists
    context['page'] = page
    context['limit'] = limit
    # テンプレートをレンダリングして返す
    return render(request, 'playlists.html', context)


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
                # print(song)
                songInfo, _ = SongInfo.objects.get_or_create(song=song, playlist=playlist)
                songInfo.order = i*2
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
            songInfo.order -= 3
            songInfo.save()
            songInfo.save()
            return redirect('app:playlist', pk=pk)
        if 'down' in post:
            # lid = post['down']
            song_pk = post['down']
            song = Song.objects.get(pk=song_pk)
            songInfo = SongInfo.objects.get(song=song, playlist=playlist)
            songInfo.order += 3
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
            order = post['order']
            song_info = SongInfo.objects.get(
                song__pk=song_pk, playlist=playlist)
            if genre != "---":
                song_info.genre = genre
            else:
                song_info.genre = None
            song_info.order = order
            song_info.save()
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
    # genres = [
    #     "---",
    #     "Acc",
    #     "Tech",
    #     "Balanced",
    #     "FullRange",
    #     "Speed",
    #     "Stamina",
    #     "Concept",
    # ]
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
        isOpen=True, isLive=True
    ).select_related(
        'owner', 'first', 'second', 'third'  # ForeignKey フィールドの名称に基づく
    ).order_by('-isOfficial', 'end', '-pk').prefetch_related('playlist')

    end_leagues = League.objects.filter(
        isOpen=True, isLive=False
    ).select_related(
        'owner', 'first', 'second', 'third'  # ForeignKey フィールドの名称に基づく
    ).order_by('-end', '-pk')
    
    context = {
        'social': social,
        'active_leagues': active_leagues,
        'end_leagues': end_leagues,
    }

    return render(request, 'leagues.html', context)

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


    # detail check
    is_detail = bool(request.GET.get('detail'))
    context['is_detail'] = is_detail
    print(is_detail)

    # prohibited leagues
    is_prohibited = False
    if player:
        user_leagues = player.league.all()
        prohibited_leagues = league.prohibited_leagues.all()
        is_prohibited = any(user_league in prohibited_leagues for user_league in user_leagues)
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
    d = defaultdict(ComparedScore)

    for score in Score.objects.filter(player=player).prefetch_related('song'):
        song = score.song
        d[song].set_my_acc(score.acc)

    for score in Score.objects.filter(player=player.rival).prefetch_related('song'):
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
    league_prefetch = Prefetch('score', queryset=Score.objects.select_related('league','song'))
    headlines = Headline.objects.prefetch_related('player',league_prefetch).order_by('-time')[start:end]
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
        isActivated=True
    ).prefetch_related(
        'badges'  # related_nameに指定された値を使用
    ).order_by(f'-{sort}', '-borderPP')
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


def info(request, pk):
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
            return redirect(f'{redirect_url}#{score.song.pk}')
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
    playlists = Playlist.objects.prefetch_related('songs').select_related('editor')
    archives = playlists.order_by('-pk').exclude(isHidden=True)
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
        league=league).order_by('-count_pos','-count_acc')
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

def archive(request):
    context = {}
    user = request.user
    if user.is_authenticated:
        social = SocialAccount.objects.get(user=user)
        context['social'] = social
    return render(request, 'archive.html', context)

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
            # if league.player.all().count() >= 2:
            #     print(league)
            #     match.league = league
            #     match.player1 = league.player.all()[0]
            #     match.player2 = league.player.all()[1]
            
            participants = Participant.objects.filter(league=league).order_by('-count_pos','-count_acc')
            
            if participants.count() >= 2:
                match.player1 = participants[0].player
                match.player2 = participants[1].player
            
            match.league = league
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

    # sorted_player
    participants = Participant.objects.filter(league=match.league).order_by('-count_pos','-count_acc')[:match.league.border_line]
    players = [participant.player for participant in participants]
    for player in players:
        print(player)
    context['players'] = players

    context['highest'] = match.highest_acc
    context['state'] = state_dict[match.state]
    context['inMatch'] = match.state % 2 == 0

    return render(request, 'match.html', context)


def api_match(request, pk):
    context = {}
    match = Match.objects.get(pk=pk)
    context['match'] = match
    info = SongInfo.objects.filter(song=match.now_playing,playlist=match.playlist).first()
    # print(info)
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
    if info.genre:
        ans['map-info1'] += f'({info.genre})'
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


def api_active_league(request):
    leagues = League.objects.filter(isLive=True,isOpen=True)
    print(leagues)
    ans = leagues.values()
    return JsonResponse(list(ans),safe=False,json_dumps_params={'ensure_ascii': False})

def api_song_info(request, pk):
    from django.forms.models import model_to_dict
    playlist = Playlist.objects.get(pk=pk)
    # song_infos = SongInfo.objects.filter(playlist=playlist).order_by('order')

    # SongInfoと関連するSongのデータを辞書のリストとして構築
    # infos_data = []
    # for info in song_infos:
    #     info_data = model_to_dict(info)  # SongInfoのインスタンスを辞書に変換
    #     info_data['song'] = model_to_dict(info.song)  # 関連するSongのインスタンスも辞書に変換
    #     infos_data.append(info_data)

    # return JsonResponse(infos_data, safe=False, json_dumps_params={'ensure_ascii': False})
    # この方法は一旦登録した info を消せないからダメ
    # 見えているプレイリストと一致するとは限らない
    # スコセイ用とビートリーダー用で分かれている場合は手動で確認＆調整
    songs = playlist.songs.all()
    songs_data = []  # JSONに変換するためのリスト
    for song in songs:
        info = song.info.filter(playlist=playlist).first()  # 各曲に対する最初のSongInfoを取得
        song_data = model_to_dict(song)  # Songインスタンスを辞書に変換
        song_data['genre'] = info.genre if info else None  # genreを追加
        songs_data.append(song_data)  # リストに追加

    return JsonResponse(songs_data, safe=False, json_dumps_params={'ensure_ascii' : False})

def api_playlist(request, pk):
    playlist = Playlist.objects.filter(pk=pk)
    ans = playlist.values()
    return JsonResponse(list(ans)[0],safe=False,json_dumps_params={'ensure_ascii': False})

def koharu_graph(request, pk):
    if os.path.exists('local.py'):
        from local import GRAPH_URL
    else:
        GRAPH_URL = os.environ['GRAPH_URL']
    image_url = f'{GRAPH_URL}{pk}.png'
    # 外部URLから画像を取得
    response = requests.get(image_url)
    # リクエストが成功した場合は画像データを返す
    if response.status_code == 200:
        return HttpResponse(response.content, content_type='image/png')
    else:
        # リクエストが失敗した場合は404エラーを返す
        return HttpResponse('Not Found', status=404)
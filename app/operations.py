import requests

from collections import defaultdict

from django.db.models import Count, Q, Max, Prefetch
from django.utils import timezone as django_timezone
from datetime import datetime

from .models import League, Participant, Player, Playlist, Song, Score, Headline, SongInfo, User, JPMap
from .utils import char_dict, hmd_dict, diff_label, col_dict, char_dict_inv, diff_label_inv
from .utils import score_to_acc, get_decorate, slope


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
    # author = res['uploader']['name']
    author = res['metadata']['levelAuthorName']
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


def top_score_registration(player : Player):
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


def make_sorted_playlist(playlist: Playlist):
    from operator import attrgetter
    sorted_songs = []
    song_infos = {song_info.song_id: song_info for song_info in SongInfo.objects.filter(playlist=playlist)}

    for song in playlist.songs.all():
        song_info = song_infos.get(song.id)
        if song_info:
            song.order = song_info.order
            song.song_info_genre = song_info.genre
        else:
            song.order = 0
            song.song_info_genre = None
        sorted_songs.append(song)

    sorted_songs.sort(key=attrgetter('order'))
    playlist.sorted_songs = sorted_songs
    print(f'Playlist {playlist} is sorted')
    return playlist

def calculate_scoredrank_LBs(league : League, virtual=None, record=False):
    
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
            song=song, league=league).filter(Q(player__league=league) | Q(player=virtual)).order_by('-score').distinct().prefetch_related('player','song')

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
    print(f'Scores of {league} is calculated')
    return players, songs


def pos_acc_update(pk):
    league = League.objects.get(pk=pk)
    print(league)
    if league.playlist == None:
        print('invalid league')
        return
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
        theoretical = 0
        if max_pos > 0:
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

def create_headline(player : Player, title, diff, old_acc=None, new_acc=None):
    if old_acc is not None:
        text = f'{player} さんが {title} ({diff}) のスコアを更新！ {old_acc:.2f} -> {new_acc:.2f} %'
    else:
        text = f'{player} さんが {title} ({diff}) のスコアを更新！ {new_acc:.2f} %'

    return Headline.objects.create(
        player=player,
        time=django_timezone.now(),
        text=text,
    )


def score_to_headline(new_score, song : Song, player : Player, league : League):
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
    

def score_acc_to_headline(new_score, acc, song : Song, player : Player, league : League):
    title = song.title[:30] + '...' if len(song.title) > 30 else song.title
    
    old_score = Score.objects.filter(
        player=player, song=song, league=league).first()

    if old_score is not None:
        if new_score > old_score.score:
            old_acc = old_score.acc
            return create_headline(player, title, song.diff, old_acc, acc)
    else:
        return create_headline(player, title, song.diff, None, acc)

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
        collect_by_player(player)

def get_love_pair_context(active_players):
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


def get_headline_and_league_context():
    context = {}
    league_prefetch = Prefetch('score__league')
    song_prefetch = Prefetch('score__song')
    # score_prefetch = Prefetch('score__league',queryset=League.objects.all()) # これでも同じだが、カスタマイズ可能。いつかこの知識が高速化に役立つかもしれない
    headlines = Headline.objects.prefetch_related(league_prefetch,song_prefetch).select_related('player').all()
    headlines = headlines.order_by('-time')[:8]
    context['headlines'] = headlines
    active_leagues = League.objects.filter(
        isOpen=True, isLive=True
    ).select_related(
        'owner', 'first', 'second', 'third', 'playlist'  # ForeignKey フィールドの名称に基づく
    ).order_by('-isOfficial', 'end', '-pk')
    context['active_leagues'] = active_leagues
    return context

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


def get_beatleader_bid(hash, dif, char):
    """
    Fetch the BeatLeader ID (bid) for a given song hash, difficulty, and game mode.

    Args:
    hash (str): The hash of the song.
    dif (str): The difficulty of the song.
    char (str): The game mode (character) of the song.

    Returns:
    int: The BeatLeader ID (bid), or -1 if not found.
    """
    url = f'https://api.beatleader.xyz/leaderboards/hash/{hash}'
    try:
        res = requests.get(url).json()
        for r in res['leaderboards']:
            res_diff = r['difficulty']['difficultyName']
            res_mode = r['difficulty']['modeName']
            if res_diff == dif and res_mode == char:
                return r['id']
    except Exception as e:
        print(f"Error while fetching BeatLeader ID: {e}")
    return -1


def add_playlist(playlist : Playlist, json_data):
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


def check_membership_and_ownership(user, league : League):
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

def collect_maps(mapper, player : Player =None):
    if mapper == 0:
        return
    print(f'collect {player}')
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

    print(f'finished {player}')

def collect_by_player(player : Player):
    collect_maps(player.mapper, player)
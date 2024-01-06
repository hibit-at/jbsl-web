import json
import os

from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import DGA, League, Match, Playlist, SongInfo
from .operations import calculate_scoredrank_LBs


def api_active_league(request):
    leagues = League.objects.filter(isLive=True, isOpen=True)
    print(leagues)
    ans = leagues.values()
    return JsonResponse(
        list(ans), safe=False, json_dumps_params={"ensure_ascii": False}
    )


def api_dga(request):
    import json

    from .models import DGA

    dgas = DGA.objects.all()
    if "sid" in request.GET:
        sid = request.GET["sid"]
        dgas = dgas.filter(sid=sid)
    if "sort" in request.GET:
        key = request.GET["sort"]
        dgas = dgas.order_by(key)
    if "limit" in request.GET:
        limit = int(request.GET["limit"])
        dgas = dgas[:limit]
    post_json = json.dumps(list(dgas.values()), ensure_ascii=False)
    return HttpResponse(post_json, content_type="application/json")


@csrf_exempt
def api_dga_post(request):
    if request.method == "GET":
        post_json = {"message": "レスポンス 200 で通信成功したと思った？ 残念！ GET じゃこの API は通りません～～～"}
        post_json = json.dumps(post_json, ensure_ascii=False)
        return HttpResponse(post_json, content_type="application/json")
    post = request.POST
    token = post["token"]
    auth = ""
    if os.path.exists("local.py"):
        from local import DGA_TOKEN

        auth = DGA_TOKEN
    else:
        auth = os.environ["DGA_TOKEN"]
    if token != auth:
        post_json = {"message": "トークン認証に失敗しました"}
        post_json = json.dumps(post_json, ensure_ascii=False)
        return HttpResponse(post_json, content_type="application/json")
    defaults = {
        "dance": float(post["dance"]),
        "gorilla": float(post["gorilla"]),
        "song_mapper": post["song_mapper"],
        "player_name": post["player_name"],
        "sid": post["sid"],
    }
    print(defaults)
    dga, check = DGA.objects.update_or_create(
        beatleader=post["beatleader"], defaults=defaults
    )
    print(check)
    if not check:
        post_json = {"message": "既にスコアが存在します"}
        post_json = json.dumps(post_json, ensure_ascii=False)
        return HttpResponse(post_json, content_type="application/json")
    post_json = {"message": "スコアを登録完了しました"}
    post_json = json.dumps(post_json, ensure_ascii=False)
    return HttpResponse(post_json, content_type="application/json")


def api_leaderboard(request, pk):
    context = {}
    league = League.objects.get(pk=pk)
    context["league"] = league
    scored_rank, LBs = calculate_scoredrank_LBs(league)
    ans = {}
    ans["league_id"] = pk
    ans["league_title"] = league.name
    ans["total_rank"] = []
    for i, rank in enumerate(scored_rank):
        ans["total_rank"].append(
            {
                "standing": i + 1,
                "sid": rank.sid,
                "name": rank.name,
                "pos": rank.count_pos,
                "acc": rank.count_acc,
            }
        )
        print(rank.name)
    ans["maps"] = []
    for LB in LBs:
        append_score = []
        for i, score in enumerate(LB.scores):
            append_score.append(
                {
                    "standing": i + 1,
                    "sid": score.player.sid,
                    "name": score.player.name,
                    "acc": score.acc,
                    "pos": score.pos,
                }
            )
        ans["maps"].append(
            {
                "title": LB.title,
                "lid": LB.lid,
                "bsr": LB.bsr,
                "scores": append_score,
            }
        )
    return HttpResponse(json.dumps(ans, indent=4, ensure_ascii=False))


def api_match(request, pk):
    context = {}
    match = Match.objects.get(pk=pk)
    context["match"] = match
    info = SongInfo.objects.filter(
        song=match.now_playing, playlist=match.playlist
    ).first()
    # print(info)
    ans = {}
    ans["title"] = match.title
    ans["player1"] = match.player1.name
    ans["player1-imageURL"] = match.player1.imageURL
    ans["player2"] = match.player2.name
    ans["player2-imageURL"] = match.player2.imageURL
    ans["result1"] = match.result1
    ans["result2"] = match.result2
    ans["retry1"] = match.retry1
    ans["retry2"] = match.retry2
    ans["imageURL"] = match.now_playing.imageURL
    ans["map-info1"] = match.now_playing.title
    if info.genre:
        ans["map-info1"] += f"({info.genre})"
    ans["map-info2"] = match.now_playing.author
    ans["map-info3"] = match.now_playing.diff
    ans["map-info3-color"] = match.now_playing.color
    ans["map-info4"] = match.map_info
    ans["state"] = match.state
    ans["highest"] = f"{match.highest_acc:.2f}"

    return HttpResponse(json.dumps(ans, indent=4, ensure_ascii=False))


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
        # 各曲に対する最初のSongInfoを取得
        info = song.info.filter(playlist=playlist).first()
        song_data = model_to_dict(song)  # Songインスタンスを辞書に変換
        song_data["genre"] = info.genre if info else None  # genreを追加
        songs_data.append(song_data)  # リストに追加

    return JsonResponse(
        songs_data, safe=False, json_dumps_params={"ensure_ascii": False}
    )


def api_playlist(request, pk):
    playlist = Playlist.objects.filter(pk=pk)
    ans = playlist.values()
    return JsonResponse(
        list(ans)[0], safe=False, json_dumps_params={"ensure_ascii": False}
    )

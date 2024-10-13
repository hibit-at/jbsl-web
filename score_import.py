import django
import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jbsl3.settings")
django.setup()

from app.models import Score, Player, JPMap, Playlist, League

player_pk_death = int(input("引き継ぎ元のプレイヤーIDを入力してください: "))
player_pk_live = int(input("引き継ぎ先のプレイヤーIDを入力してください: "))

# プレイヤーの名前を取得して表示
death_player_name = Player.objects.get(pk=player_pk_death).name
live_player_name = Player.objects.get(pk=player_pk_live).name

print(f"引き継ぎ元のプレイヤー: {death_player_name}")
print(f"引き継ぎ先のプレイヤー: {live_player_name}")

# スコアを引き継ぐ前にスコア数を確認
death_scores = Score.objects.filter(player__pk=player_pk_death)
live_scores = Score.objects.filter(player__pk=player_pk_live)

print(f"引き継ぎ元のスコア数: {death_scores.count()}")
print(f"引き継ぎ先のスコア数: {live_scores.count()}")

# 最終確認
confirmation = input("引き継ぎを実行しますか？ (y/n): ")

if confirmation != 'y':
    exit()

# 引き継ぎ先に存在しないスコアを探す
for score in death_scores:
    # 引き継ぎ先の同じ曲・リーグのスコアが存在するか確認
    exists = live_scores.filter(song=score.song, league=score.league).exists()
    
    if not exists:
        # 新しいスコアオブジェクトを作成
        new_score = Score(
            player_id=player_pk_live,
            song=score.song,
            league=score.league,
            score=score.score,
            acc=score.acc,
            rawPP=score.rawPP,
            miss=score.miss,
            comment=score.comment,
            rank=score.rank,
            pos=score.pos,
            weight_acc=score.weight_acc,
            decorate=score.decorate,
            valid=score.valid,
            beatleader=score.beatleader
        )
        # 新しいスコアを保存
        new_score.save()

# スコアを確認するために出力
for score in Score.objects.filter(player__pk=player_pk_live):
    print(score)
    
# JPMapの設定を引き継ぐ
jp_maps = JPMap.objects.filter(uploader__pk=player_pk_death)

for jp_map in jp_maps:
    print(jp_map)
    jp_map.uploader_id = player_pk_live
    jp_map.save()

# Playlistの設定を引き継ぐ
playlists = Playlist.objects.filter(editor__pk=player_pk_death)

for playlist in playlists:
    print(playlist)
    playlist.editor_id = player_pk_live
    playlist.save()

# CoEditorフィールドの更新
playlists_coeditor = Playlist.objects.filter(CoEditor__pk=player_pk_death)

for playlist in playlists_coeditor:
    print(playlist)
    playlist.CoEditor.remove(player_pk_death)
    playlist.CoEditor.add(player_pk_live)
    
# Leagueの設定を引き継ぐ
leagues = League.objects.filter(owner__pk=player_pk_death) | \
            League.objects.filter(first__pk=player_pk_death) | \
            League.objects.filter(second__pk=player_pk_death) | \
            League.objects.filter(third__pk=player_pk_death) | \
            League.objects.filter(player__pk=player_pk_death) | \
            League.objects.filter(invite__pk=player_pk_death) | \
            League.objects.filter(virtual__pk=player_pk_death)

for league in leagues:
    print(league)
    if league.owner_id == player_pk_death:
        league.owner_id = player_pk_live
    if league.first_id == player_pk_death:
        league.first_id = player_pk_live
    if league.second_id == player_pk_death:
        league.second_id = player_pk_live
    if league.third_id == player_pk_death:
        league.third_id = player_pk_live

    player_death = Player.objects.get(pk=player_pk_death)
    if player_death in league.player.all():
        league.player.remove(player_pk_death)
        league.player.add(player_pk_live)

    if player_death in league.invite.all():
        league.invite.remove(player_pk_death)
        league.invite.add(player_pk_live)

    if player_death in league.virtual.all():
        league.virtual.remove(player_pk_death)
        league.virtual.add(player_pk_live)

    league.save()
    
player_death = Player.objects.get(pk=player_pk_death)
player_death.delete()
import os
from datetime import datetime

import pytz

from utils import setup_django



def initialize_social_app():
    from allauth.socialaccount.models import SocialApp
    from django.contrib.sites.models import Site
    from local import SOCIALAPP_NAME, SOCIALCLIENT_ID, SOCIALSECRETKEY

    # 既に同じ名前とプロバイダーを持つ SocialApp が存在するかをチェック
    if SocialApp.objects.filter(provider="discord", name=SOCIALAPP_NAME).exists():
        print(f"SocialApp '{SOCIALAPP_NAME}' with provider 'discord' already exists.")
        return

    # SocialApp オブジェクトを作成
    social_app = SocialApp.objects.create(
        provider="discord",
        name=SOCIALAPP_NAME,
        client_id=SOCIALCLIENT_ID,
        secret=SOCIALSECRETKEY,
        key="",
    )
    print(f"SocialApp '{SOCIALAPP_NAME}' created successfully.")

    # Site オブジェクトを取得し、SocialApp に関連付ける
    try:
        site = Site.objects.get(id=2)  # 既存の Site オブジェクトを取得
        social_app.sites.add(site)
        print(f"Site with id 2 has been associated with '{SOCIALAPP_NAME}'.")
    except Site.DoesNotExist:
        print(
            "Site with id 2 does not exist. SocialApp was not associated with any site."
        )


def create_top10_league():
    name = 'Top10'
    from app.models import League
    league = League.objects.filter(name=name).first()
    if not league:
        league = League.objects.create(
            name=name,
            owner=None,
            description="",
            color="",
            max_valid=0,
            limit=2000,
            end=datetime.now(pytz.utc),
            isPermanent=False,
            isOpen=False,
            isPublic=False,
            isLive=False,
            playlist=None,
            first=None,
            second=None,
            third=None,
            isOfficial=False,
            ownerComment="",
            border_line=8,
        )
        print(f"league {league} created!")
    return league
    

def make_first_player_superuser():
    from app.models import Player

    # 最初に登録されたプレイヤーを取得
    first_player = Player.objects.order_by("pk").first()
    first_user = first_player.user
    if first_user is not None:
        # スーパーユーザー権限を付与
        first_user.is_staff = True
        first_user.is_superuser = True
        first_user.save()
        print(f"{first_user.username} にスーパーユーザー権限が付与されました。")
        return first_player
    else:
        print("登録されたユーザーが存在しません。")
        return None


def create_dummy_playlist(player):
    from app.models import Playlist
    dummy_league_names = ["JP Weekly", "JP Biweekly", "JP Latest"]
    for name in dummy_league_names:
        playlist = Playlist.objects.filter(title=name).first()
        if not playlist:
            playlist = Playlist.objects.create(
                title=name,
                editor=player,
                image="",
                description="",
                isEditable=False,
                isHidden=False,
            )
            print(f"playlist {playlist} created!")


def cretae_dummy_league(name: str, playlist):
    from app.models import League

    league = League.objects.filter(name=name).first()
    if not league:
        league = League.objects.create(
            name=name,
            owner=None,
            description="",
            color="",
            max_valid=0,
            limit=2000,
            end=datetime.now(pytz.utc),
            isPermanent=False,
            isOpen=False,
            isPublic=True,
            isLive=True,
            playlist=playlist,
            first=None,
            second=None,
            third=None,
            isOfficial=False,
            ownerComment="",
            border_line=8,
        )
        print(f"league {league} created!")
    return league


if __name__ == "__main__":
    if not os.path.exists("local.py"):
        print("initialize can be done only in local")
        exit()
    setup_django()
    initialize_social_app()
    create_top10_league()
    print("Webサービス上で最初のユーザー登録してください。そのユーザーをスーパーユーザーとします")
    input()
    superplayer = make_first_player_superuser()
    create_dummy_playlist(superplayer)

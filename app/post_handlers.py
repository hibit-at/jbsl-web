from .models import League, Player, User, Song
from django.shortcuts import redirect, render
from django.http import HttpRequest, QueryDict
from allauth.socialaccount.models import SocialAccount

import requests

from .utils import validation
from .operations import process_mapper


def post_index(post: QueryDict, player: Player):
    """Handle POST requests for joining or declining leagues."""
    print(post)

    if "join" in post and post["join"]:
        league = League.objects.get(pk=post["join"])
        league.player.add(player)
        league.invite.remove(player)
        return redirect("app:leaderboard", pk=league.pk)

    if "decline" in post and post["decline"]:
        league = League.objects.get(pk=post["decline"])
        league.invite.remove(player)
        return redirect("app:index")

    return None


def post_leaderboard(post: QueryDict, league: League):
    print(post)
    if "join" in post and post["join"] != "":
        sid = post["join"]
        add_player = Player.objects.get(sid=sid)
        league.player.add(add_player)
        return redirect("app:leaderboard", pk=league.pk)
    if "disjoin" in post and post["disjoin"] != "":
        sid = post["disjoin"]
        remove_player = Player.objects.get(sid=sid)
        league.player.remove(remove_player)
        return redirect("app:leaderboard", pk=league.pk)
    if "remove_song" in post and post["remove_song"] != "":
        song_pk = post["remove_song"]
        playlist = league.playlist
        playlist.songs.remove(Song.objects.get(pk=song_pk))
        return redirect("app:leaderboard", pk=league.pk)


def post_userpage(post: QueryDict, user: User, player: Player, context: dict):
    player.message = (
        validation(post["message"][:50]) if "message" in post else player.message
    )
    social = SocialAccount.objects.get(user=player.user)
    player.twitter = post.get("twitter", player.twitter)
    player.twitch = post.get("twitch", player.twitch)
    player.booth = post.get("booth", player.booth)
    if "rival" in post:
        user.player.rival = player
        user.player.save()
        return redirect("app:rivalpage")
    if "icon_scoresaber" in post:
        url = f"https://scoresaber.com/api/player/{player.sid}/basic"
        res = requests.get(url).json()
        imageURL = res["profilePicture"]
        player.imageURL = imageURL
    if "icon_discord" in post:
        if social.extra_data["avatar"] != None:
            player.imageURL = f'https://cdn.discordapp.com/avatars/{social.uid}/{social.extra_data["avatar"]}'
    player.userColor = post.get("color", player.userColor)
    player.bgColor = post.get("bg", player.bgColor)
    player.isShadow = "shadow" in post

    if "mapper" in post:
        mapper_id = post["mapper"]
        process_mapper(mapper_id, player, context)

    player.save()
    return None

import asyncio
import os
import django

from discord_utils import get_discord_config, get_discord_bot

from utils import setup_django


async def fetch_member_ids(guild_id, token):
    bot = get_discord_bot()
    member_ids = []

    @bot.event
    async def on_ready():
        print("Logged in as {0}".format(bot.user))
        guild = bot.get_guild(int(guild_id))
        member_ids.extend([member.id for member in guild.members])
        await bot.close()

    await bot.start(token)
    return member_ids


def update_player_records(member_ids):
    from app.models import Player
    from allauth.socialaccount.models import SocialAccount

    for discord_id in member_ids:
        social = SocialAccount.objects.filter(uid=discord_id).first()
        if not social:
            continue  # ソーシャルアカウントが存在しなければ次のIDへ

        user = social.user
        player = Player.objects.filter(user=user).first()
        if not player:
            continue  # プレイヤーが存在しなければ次のIDへ

        if player.inDiscord:
            print(f"{user} already counted")
        else:
            print(f"{user} new count")
            player.inDiscord = True
            player.save()

    print("\nwho is not in?\n")
    for player in Player.objects.all():
        user = player.user
        social = user.socialaccount_set.first()
        if social and int(social.uid) not in member_ids:
            print(f"{player} ({social}) is not in discord")


def sync_discord_members_with_django():
    setup_django()
    guild_id, token = get_discord_config()
    member_ids = asyncio.run(fetch_member_ids(guild_id, token))
    update_player_records(member_ids)


if __name__ == "__main__":
    sync_discord_members_with_django()

# import os
# import django
# import sys

# def discord_check_process():
#     os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbsl3.settings')
#     django.setup()
#     import discord
#     from discord.ext import commands
#     from app.models import Player, User
#     from allauth.socialaccount.models import SocialAccount
#     import asyncio
#     if os.path.exists('local.py'):
#         from local import DISCORD_BOT_TOKEN, GUILD_ID
#         guild_id = GUILD_ID
#         token = DISCORD_BOT_TOKEN
#     else:
#         guild_id = os.getenv('GUILD_ID')
#         token = os.getenv('DISCORD_BOT_TOKEN')
#     intents = discord.Intents.all()
#     intents.members = True
#     bot = commands.Bot(command_prefix='/', intents=intents)

#     # メンバーIDを格納するグローバル変数のリストを定義する
#     member_ids = []

#     @bot.event
#     async def on_ready():
#         # ログインが完了したときに呼び出される関数
#         print('Logged in as {0}'.format(bot.user))
#         # サーバーのメンバーのIDを取得してグローバル変数のリストに追加する   
#         async def add_member_id(member_ids, member):
#             member_ids.append(member.id)   
#         guild = bot.get_guild(int(guild_id))
#         tasks = []
#         for member in guild.members:
#             tasks.append(add_member_id(member_ids, member))
#         await asyncio.gather(*tasks)
#         await bot.close()

#     # Discordにログインする
#     bot.run(token)

#     for discord_id in member_ids:
#         social = SocialAccount.objects.filter(uid=discord_id).first()
#         if social:
#             user = social.user
#             player = Player.objects.filter(user=user).first()
#             if player:
#                 if player.inDiscord:
#                     print(f'{user} already counted')
#                 else:
#                     print(f'{user} new count')
#                     player.inDiscord = True
#                     player.save()
    
#     print('\nwho is not in?\n')

#     for player in Player.objects.all():
#         user : User = player.user
#         social = user.socialaccount_set.first()
#         if social:
#             if not int(social.uid) in member_ids:
#                 print(f'{player} ({social}) is not in discord')


# if __name__ == '__main__':
#     discord_check_process()


import asyncio
import os
import django
import discord
from discord.ext import commands
from discord_utils import get_discord_config

def setup_django():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbsl3.settings')
    django.setup()

async def fetch_member_ids(guild_id, token):
    intents = discord.Intents.all()
    intents.members = True
    bot = commands.Bot(command_prefix='/', intents=intents)
    member_ids = []

    @bot.event
    async def on_ready():
        print('Logged in as {0}'.format(bot.user))
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
            print(f'{user} already counted')
        else:
            print(f'{user} new count')
            player.inDiscord = True
            player.save()


    print('\nwho is not in?\n')
    for player in Player.objects.all():
        user = player.user
        social = user.socialaccount_set.first()
        if social and int(social.uid) not in member_ids:
            print(f'{player} ({social}) is not in discord')

def sync_discord_members_with_django():
    setup_django()
    guild_id, token = get_discord_config()
    member_ids = asyncio.run(fetch_member_ids(guild_id, token))
    update_player_records(member_ids)

if __name__ == '__main__':
    sync_discord_members_with_django()

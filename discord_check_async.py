import os
import django
import sys
import asyncio
from channels.db import database_sync_to_async

@database_sync_to_async
def get_players_not_in_discord():
    from app.models import Player
    return Player.objects.filter(inDiscord=False)

@database_sync_to_async
def update_player_in_discord(player):
    player.inDiscord = True
    player.save()

async def discord_check_process():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbsl3.settings')
    django.setup()
    import discord
    from discord.ext import commands
    from app.models import Player
    from allauth.socialaccount.models import SocialAccount
    if os.path.exists('local.py'):
        from local import DISCORD_BOT_TOKEN, GUILD_ID
        guild_id = GUILD_ID
        token = DISCORD_BOT_TOKEN
    else:
        guild_id = os.getenv('GUILD_ID')
        token = os.getenv('DISCORD_BOT_TOKEN')
    intents = discord.Intents.all()
    intents.members = True
    bot = commands.Bot(command_prefix='/', intents=intents)

    @bot.event
    async def on_ready():
        guild = bot.get_guild(int(guild_id))
        members = guild.members
        joinIDs = [member.id for member in members]
        players_not_in_discord = await get_players_not_in_discord()

        for player in players_not_in_discord:
            from allauth.socialaccount.models import SocialAccount
            social = SocialAccount.objects.get(user=player.user)
            print(social)
            if int(social.uid) in joinIDs:
                print('joined')
                await update_player_in_discord(player)
        await bot.close()

    await bot.start(token)

if __name__ == '__main__':
    asyncio.run(discord_check_process())
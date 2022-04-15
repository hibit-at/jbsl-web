import os
import django
import sys


def league_distribution():
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
    intents = discord.Intents.default()
    intents.members = True
    bot = commands.Bot(command_prefix='/', intents=intents)

    @bot.event
    async def on_ready():
        guild = bot.get_guild(int(guild_id))
        members = guild.members
        for member in members:
            if not Player.objects.filter(discordID=member.id).exists():
                continue
            player = Player.objects.get(discordID=member.id)
            print(player)
            pp = player.borderPP
            if 1050 <= pp:
                role = discord.utils.get(guild.roles,name="J1")
                print(role)
                await member.add_roles(role)
            elif 800 <= pp:
                role = discord.utils.get(guild.roles,name="J2")
                print(role)
                await member.add_roles(role)
            else:
                role = discord.utils.get(guild.roles,name="J3")
                print(role)
                await member.add_roles(role)
        await bot.close()

    bot.run(token)


if __name__ == '__main__':
    league_distribution()

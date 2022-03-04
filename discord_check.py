import os
import django
import sys

def discord_check_process(channel_id):
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
        guild = bot.get_guild(guild_id)
        channel = await bot.fetch_channel(channel_id)
        members = guild.members
        print(guild)
        joinIDs = [member.id for member in members]
        print(joinIDs)
        for player in Player.objects.filter(inDiscord=False):
            social = SocialAccount.objects.get(user=player.user)
            print(social)
            if int(social.uid) in joinIDs:
                await channel.send(f'{player} さんはすでに Discord に参加しています。')
                player.inDiscord = True
                player.save()
                await channel.send(f'内部データベースを参加状態にしました。')
            else:
                await channel.send(f'{player} さんはまだ Discord に参加していません。')

    bot.run(token)


if __name__ == '__main__':
    args = sys.argv
    send_channel_id = int(args[1])
    discord_check_process(send_channel_id)

import os
import django
from collections import defaultdict


def process():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbsl3.settings')
    django.setup()
    from app.models import Player
    from allauth.socialaccount.models import SocialAccount
    socials = SocialAccount.objects.all()
    import discord
    from discord.ext import commands
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

    from_id_to_avatar = defaultdict(str)

    @bot.event
    async def on_ready():
        guild = bot.get_guild(int(guild_id))
        print(guild)
        for member in guild.members:
            print(member)
            from_id_to_avatar[member.id] = member.avatar
        print(from_id_to_avatar)
        for player in Player.objects.all():
            print(player)
            if not int(player.discordID) in from_id_to_avatar:
                print('not in discord!')
                continue
            imageURL = player.imageURL
            if imageURL.startswith('https://cdn.discordapp.com'):
                new_image = from_id_to_avatar[int(player.discordID)]
                if type(new_image) == str:
                    continue
                new_image = new_image.url.split('?')[0]
                print(new_image)
                if player.imageURL != new_image:
                    player.imageURL = new_image
                    player.save()
        await bot.close()

    bot.run(token)


if __name__ == '__main__':
    process()

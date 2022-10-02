import os
import django


def role_add(ID,role_name):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbsl3.settings')
    django.setup()
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

    @bot.event
    async def on_ready():
        guild = bot.get_guild(int(guild_id))
        member = guild.get_member(ID)
        role = discord.utils.get(guild.roles,name=role_name)
        print(member)
        print(role)
        await member.add_roles(role)
        await bot.close()

    bot.run(token)


if __name__ == '__main__':
    ID = 435010295899881473
    role_name = 'Supporter'
    role_add(ID,role_name)

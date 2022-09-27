import os
import django


def league_erase():
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
    intents = discord.Intents.default()
    intents.members = True
    bot = commands.Bot(command_prefix='/', intents=intents)

    @bot.event
    async def on_ready():
        guild = bot.get_guild(int(guild_id))
        members = guild.members
        for member in members:
            print(member.name)
            role_names = ["J1","J2","J3","J1本戦","J2本戦","J3本戦"]
            for role_name in role_names:
                role = discord.utils.get(guild.roles,name=role_name)
                await member.remove_roles(role)
        await bot.close()

    bot.run(token)


if __name__ == '__main__':
    league_erase()

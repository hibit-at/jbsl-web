import os
import django


def league_create(league_name):
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
        category = discord.utils.get(guild.categories, name='test')
        print(category)
        await category.create_text_channel(league_name)
        await bot.close()

    bot.run(token)


if __name__ == '__main__':
    league_name = '精神と時の部屋'
    league_create(league_name)

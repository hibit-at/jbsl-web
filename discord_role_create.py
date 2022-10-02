import os
import django


def role_create(role_name, color_string):
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

    {'value': 'lightblue', 'text': 'Blue'},
    {'value': 'lightgreen', 'text': 'Green'},
    {'value': 'lightsalmon', 'text': 'Orange'},
    {'value': 'lightpink', 'text': 'Red'},
    {'value': '#FFCCFF', 'text': 'Purple'},
    {'value': 'lightyellow', 'text': 'Yellow'},

    @bot.event
    async def on_ready():
        guild = bot.get_guild(int(guild_id))
        colour = discord.Colour.default()
        col_dict = {}
        col_dict['lightblue'] = discord.Colour.blue()
        col_dict['lightgreen'] = discord.Colour.green()
        col_dict['lightsalmon'] = discord.Colour.orange()
        col_dict['lightpink'] = discord.Colour.red()
        col_dict['#FFCCFF'] = discord.Colour.purple()
        col_dict['lightyellow'] = discord.Colour.gold()
        if color_string in col_dict:
            colour = col_dict[color_string]
        await guild.create_role(name=role_name, colour=colour)
        await bot.close()

    bot.run(token)


if __name__ == '__main__':
    role_name = 'test_role'
    color_string = 'lightblue'
    role_create(role_name, color_string)

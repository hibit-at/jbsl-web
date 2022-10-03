import os
import django


def discord_message_process(message_text):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbsl3.settings')
    django.setup()
    import discord
    from discord.ext import commands
    if os.path.exists('local.py'):
        from local import DISCORD_BOT_TOKEN, NOTIFY_ID
        token = DISCORD_BOT_TOKEN
        channel_id = NOTIFY_ID
    else:
        token = os.getenv('DISCORD_BOT_TOKEN')
        channel_id = os.getenv('NOTIFY_ID')
    intents = discord.Intents.default()
    intents.members = True
    bot = commands.Bot(command_prefix='/', intents=intents)

    @bot.event
    async def on_ready():
        channel = await bot.fetch_channel(channel_id)
        await channel.send(message_text)
        await bot.close()

    bot.run(token)


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
            role_names = ["J1", "J2", "J3", "J1本戦", "J2本戦", "J3本戦"]
            for role_name in role_names:
                role = discord.utils.get(guild.roles, name=role_name)
                await member.remove_roles(role)
        await bot.close()

    bot.run(token)


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


def role_add(ID, role_name):
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
        role = discord.utils.get(guild.roles, name=role_name)
        print(member)
        print(role)
        await member.add_roles(role)
        await bot.close()

    bot.run(token)


if __name__ == '__main__':
    print('utils manual test')
    # league_erase()

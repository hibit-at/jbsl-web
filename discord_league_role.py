from datetime import timedelta,datetime
import os
import django
import asyncio

def name_validation(valid_name):
    valid_name = valid_name.lower().replace(' ', '-')
    valid_name = valid_name.replace('[','')
    valid_name = valid_name.replace(']','')
    valid_name = valid_name.replace('.','')
    valid_name = valid_name.replace('!','')
    valid_name = valid_name.replace('/','')
    valid_name = valid_name.strip()
    return valid_name

async def league_create(league_name, league_end, league_id, league_color, player_dIDs):
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
        category = discord.utils.get(guild.categories, name='進行中リーグ')
        role_names = []
        for role in guild.roles:
            role_names.append(role.name)
        print(role_names)
        channels = category.channels
        exist = any(channel.name == league_name for channel in channels)
        if not exist:
            current_channel = await category.create_text_channel(league_name)
            gmt_time = league_end + timedelta(hours=9)
            y = gmt_time.year
            m = gmt_time.month
            d = gmt_time.day
            h = gmt_time.hour
            M = gmt_time.minute
            content = f'{league_name} リーグが開催されました！\n 終了日時は {y}/{m}/{d} {h}:{M} です！\n https://jbsl-web.herokuapp.com/leaderboard/{league_id}'
            await current_channel.send(content)
        if not league_name in role_names:
            colour = discord.Colour.default()
            col_dict = {}
            col_dict['rgba(130,211,255,.8)'] = discord.Colour.blue()
            col_dict['rgba(207,130,255,.8'] = discord.Colour.green()
            col_dict['rgba(255,128,60,.8)'] = discord.Colour.orange()
            col_dict['rgba(255,128,128,.8)'] = discord.Colour.red()
            col_dict['rgba(220,130,250,.8)'] = discord.Colour.purple()
            col_dict['rgba(255,255,128,.8)'] = discord.Colour.gold()
            if league_color in col_dict:
                colour = col_dict[league_color]
            await guild.create_role(name=league_name, colour=colour, hoist=True)

        everyone = discord.utils.get(guild.roles, name='@everyone')
        current_channel = discord.utils.get(
            guild.channels, name=league_name)
        current_role = discord.utils.get(guild.roles, name=league_name)
        print(current_channel)
        print(current_role)
        await current_channel.set_permissions(everyone, send_messages=False)
        await current_channel.set_permissions(current_role, send_messages=True)

        for player_dID in player_dIDs:
            print(player_dID)
            member = guild.get_member(int(player_dID))
            if member is None:
                continue
            await member.add_roles(current_role)

        # await bot.close()

    try:
        await asyncio.wait_for(bot.start(token), timeout=10)
    except asyncio.TimeoutError:
        print('タイムアウトしました。')


def league_role_total():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbsl3.settings')
    django.setup()
    from app.models import League

    leagues = League.objects.filter(isLive=True)
    for league in League.objects.filter(isLive=True):
        valid_name = name_validation(league.name)
        players = league.player.all()
        player_dIDs = [player.discordID for player in players]
        asyncio.run(league_create(valid_name,league.end,league.id,league.color,player_dIDs))



    # for league in League.objects.filter(isLive=True):
    #     valid_name = league.name.lower().replace(' ', '-')
    #     valid_name = valid_name.replace('[','')
    #     valid_name = valid_name.replace(']','')
    #     valid_name = valid_name.replace('.','')
    #     valid_name = valid_name.replace('!','')
    #     valid_name = valid_name.replace('/','')
    #     valid_name = valid_name.strip()
    #     print(valid_name)
    #     if not valid_name in channel_names:
    #         current_channel = await category.create_text_channel(valid_name)
    #         gmt_time = league.end + timedelta(hours=9)
    #         y = gmt_time.year
    #         m = gmt_time.month
    #         d = gmt_time.day
    #         h = gmt_time.hour
    #         M = gmt_time.minute
    #         content = f'{league.name} リーグが開催されました！\n 終了日時は {y}/{m}/{d} {h}:{M} です！\n https://jbsl-web.herokuapp.com/leaderboard/{league.id}'
    #         await current_channel.send(content)
    #     if not league.name in role_names:
    #         colour = discord.Colour.default()
    #         col_dict = {}
    #         col_dict['rgba(130,211,255,.8)'] = discord.Colour.blue()
    #         col_dict['rgba(207,130,255,.8'] = discord.Colour.green()
    #         col_dict['rgba(255,128,60,.8)'] = discord.Colour.orange()
    #         col_dict['rgba(255,128,128,.8)'] = discord.Colour.red()
    #         col_dict['rgba(220,130,250,.8)'] = discord.Colour.purple()
    #         col_dict['rgba(255,255,128,.8)'] = discord.Colour.gold()
    #         if league.color in col_dict:
    #             colour = col_dict[league.color]
    #         await guild.create_role(name=league.name, colour=colour, hoist=True)

    #     everyone = discord.utils.get(guild.roles, name='@everyone')
    #     current_channel = discord.utils.get(
    #         guild.channels, name=valid_name)
    #     current_role = discord.utils.get(guild.roles, name=league.name)
    #     print(current_channel)
    #     print(current_role)
    #     await current_channel.set_permissions(everyone, send_messages=False)
    #     await current_channel.set_permissions(current_role, send_messages=True)

    #     for player in league.player.all():
    #         print(player.discordID)
    #         member = guild.get_member(int(player.discordID))
    #         if member is None:
    #             continue
    #         await member.add_roles(current_role)


if __name__ == '__main__':
    league_role_total()

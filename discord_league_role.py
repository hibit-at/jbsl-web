import os
import django

def league_role_total():
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

    from app.models import League

    @bot.event
    async def on_ready():
        guild = bot.get_guild(int(guild_id))
        category = discord.utils.get(guild.categories, name='進行中リーグ')
        channel_names = []
        role_names = []
        for channel in category.channels:
            channel_names.append(channel.name)
        for role in guild.roles:
            role_names.append(role.name)
        for league in League.objects.filter(isLive=True):
            if not league.name in channel_names:
                await category.create_text_channel(league.name)
            if not league.name in role_names:
                colour = discord.Colour.default()
                col_dict = {}
                col_dict['lightblue'] = discord.Colour.blue()
                col_dict['lightgreen'] = discord.Colour.green()
                col_dict['lightsalmon'] = discord.Colour.orange()
                col_dict['lightpink'] = discord.Colour.red()
                col_dict['#FFCCFF'] = discord.Colour.purple()
                col_dict['lightyellow'] = discord.Colour.gold()
                if league.color in col_dict:
                    colour = col_dict[league.color]
                await guild.create_role(name=league.name, colour=colour)
            
            current_role = discord.utils.get(guild.roles, name=league.name)
            print(current_role)

            for player in league.player.all():
                print(player.discordID)
                member = guild.get_member(int(player.discordID))
                await member.add_roles(current_role)
            print(member)
                
        await bot.close()

    bot.run(token)

if __name__ == '__main__':
    league_role_total()

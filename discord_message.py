import os
import django
import sys

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


if __name__ == '__main__':
    args = sys.argv
    message_text = args[1]
    discord_message_process(message_text)

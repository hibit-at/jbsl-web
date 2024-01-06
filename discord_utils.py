import asyncio
import os

import discord
import django
from discord.ext import commands


def discord_validation(valid_name):
    valid_name = valid_name.lower().replace(" ", "-")
    valid_name = valid_name.replace("[", "")
    valid_name = valid_name.replace("]", "")
    valid_name = valid_name.replace(".", "")
    valid_name = valid_name.replace("!", "")
    valid_name = valid_name.replace("/", "")
    valid_name = valid_name.replace("(", "")
    valid_name = valid_name.replace(")", "")
    valid_name = valid_name.strip()
    return valid_name


def get_discord_config():
    if os.path.exists("local.py"):
        from local import DISCORD_BOT_TOKEN, GUILD_ID

        return GUILD_ID, DISCORD_BOT_TOKEN
    return os.getenv("GUILD_ID"), os.getenv("DISCORD_BOT_TOKEN")


def get_discord_bot():
    intents = discord.Intents.default()
    intents.members = True
    bot = commands.Bot(command_prefix="/", intents=intents)
    return bot


def discord_message_process_with_channel(message_text, channel_name):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "jbsl3.settings")
    django.setup()

    if os.path.exists("local.py"):
        from local import DISCORD_BOT_TOKEN, GUILD_ID

        guild_id = GUILD_ID
        token = DISCORD_BOT_TOKEN
    else:
        guild_id = os.getenv("GUILD_ID")
        token = os.getenv("DISCORD_BOT_TOKEN")

    channel_name = discord_validation(channel_name)
    intents = discord.Intents.default()
    intents.members = True
    bot = commands.Bot(command_prefix="/", intents=intents)

    @bot.event
    async def on_ready():
        guild = bot.get_guild(int(guild_id))
        category = discord.utils.get(guild.categories, name="進行中リーグ")
        target_channel = None
        print(category.text_channels)
        for channel in category.text_channels:
            if channel.name == channel_name:
                target_channel = channel
        if target_channel is not None:
            await target_channel.send(message_text)
        await bot.close()

    bot.run(token)


def discord_message_process(input_message):
    message_texts = []
    # 文字列が単一のメッセージであれば、リストに変換
    if isinstance(input_message, str):
        message_texts = [input_message]
    else:
        message_texts = input_message

    if os.path.exists("local.py"):
        from local import DISCORD_BOT_TOKEN, NOTIFY_ID

        token = DISCORD_BOT_TOKEN
        channel_id = 947759671844933652  # local test
    else:
        token = os.getenv("DISCORD_BOT_TOKEN")
        channel_id = os.getenv("NOTIFY_ID")

    intents = discord.Intents.default()
    intents.members = True
    bot = commands.Bot(command_prefix="/", intents=intents)

    async def send_messages(channel, messages):
        for message in messages:
            await channel.send(message)

    @bot.event
    async def on_ready():
        channel = await bot.fetch_channel(channel_id)
        await asyncio.gather(send_messages(channel, message_texts))
        await bot.close()

    bot.run(token)


if __name__ == "__main__":
    print("utils manual test")

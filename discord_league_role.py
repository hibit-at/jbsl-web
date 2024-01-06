import asyncio
import os
from datetime import timedelta

import discord

from discord_utils import discord_validation, get_discord_bot

from utils import setup_django

DEBUG = False
if os.path.exists("local.py"):
    DEBUG = True


col_dict = {
    "rgba(130,211,255,.8)": discord.Colour.blue(),
    "rgba(207,130,255,.8)": discord.Colour.green(),
    "rgba(255,128,60,.8)": discord.Colour.orange(),
    "rgba(255,128,128,.8)": discord.Colour.red(),
    "rgba(220,130,250,.8)": discord.Colour.purple(),
    "rgba(255,255,128,.8)": discord.Colour.gold(),
    # 他の色を追加する場合は、以下の形式で追加します
    # 'RGBA色コード': discord.Colour.適切な色()
}


async def get_or_create_role(bot, guild, league_name, color):
    # 同名のロールが存在するか確認
    existing_role = discord.utils.get(guild.roles, name=league_name)
    if existing_role is not None:
        print(f"ロール '{league_name}' は既に存在します。")
        return existing_role
    # 新しいロールを作成
    if DEBUG:
        print(f"デバッグ：本番環境では {league.name} ロールを作成します。")
        return None
        # 実際にロールを作って実験する場合は以下の処理
        new_role = await guild.create_role(name=league_name, color=color)
        print(f"ロール '{league_name}' を作成しました。")
        return new_role
    else:
        new_role = await guild.create_role(name=league_name, color=color)
        print(f"ロール '{league_name}' を作成しました。")
        return new_role


async def apply_role_members(bot, guild, role, member_ids):
    print(role)
    for member_id in member_ids:
        # メンバーIDに基づいてメンバーを取得
        member = guild.get_member(int(member_id))
        if member is not None:
            if DEBUG:
                print(f"デバッグ：本番環境では '{role.name}' をメンバー '{member.display_name}' に付与します")
            else:
                await member.add_roles(role)
                print(f"ロール '{role.name}' をメンバー '{member.display_name}' に付与しました。")
        else:
            print(f"メンバーID '{member_id}' に該当するメンバーが見つかりません。")


def get_channel_message(league_name, end, pk):
    gmt_time = end + timedelta(hours=9)
    return f"{league_name} リーグが開催されました！\n終了日時は {gmt_time:%Y/%m/%d %H:%M} です！\nhttps://jbsl-web.herokuapp.com/leaderboard/{pk}"


async def get_or_create_channel(bot, guild, category_name, league_name, end, pk):
    # カテゴリを取得
    category = discord.utils.get(guild.categories, name=category_name)
    if category is None:
        print(f"カテゴリ '{category_name}' が見つかりません。")
        return None
    # 同名のチャンネルが存在するか確認
    existing_channel = discord.utils.get(category.channels, name=league_name)
    if existing_channel is not None:
        print(f"チャンネル '{league_name}' は既に存在します。")
        return existing_channel
    # 新しいチャンネルを作成
    message = get_channel_message(league_name, end, pk)
    if DEBUG:
        print(f"デバッグ：本番環境では {league.name} チャンネルを作成します。")
        return None
        # スタッフカテゴリに実際にチャンネルを作って実験する場合は以下の処理
        dummy_new_channel = await category.create_text_channel(league_name)
        print(f"チャンネル '{league_name}' を作成しました。")
        await dummy_new_channel.send(message)
        return dummy_new_channel
    else:
        new_channel = await category.create_text_channel(league_name)
        print(f"チャンネル '{league_name}' を作成しました。")
        await new_channel.send(message)
        return new_channel


async def set_channel_permissions_for_role(channel, role):
    # @everyone ロールに対してメッセージ送信権限を無効化
    await channel.set_permissions(channel.guild.default_role, send_messages=False)
    # 指定されたロールに対してメッセージ送信権限を有効化
    await channel.set_permissions(role, send_messages=True)
    print("channel permission set")


def load_config():
    if DEBUG:
        from local import DISCORD_BOT_TOKEN, GUILD_ID, NOTIFY_ID

        return DISCORD_BOT_TOKEN, 947759671844933652, GUILD_ID, "スタッフ"
    else:
        return (
            os.getenv("DISCORD_BOT_TOKEN"),
            os.getenv("NOTIFY_ID"),
            os.getenv("GUILD_ID"),
            "進行中リーグ",
        )

async def league_process(league_data):
    token, channel_id, guild_id, category_name = load_config()
    bot = get_discord_bot()
    valid_name, end, pk, color, member_ids = league_data

    @bot.event
    async def on_ready():
        guild = bot.get_guild(int(guild_id))
        role = await get_or_create_role(bot, guild, valid_name, color)
        await apply_role_members(bot, guild, role, member_ids)
        channel = await get_or_create_channel(
            bot, guild, category_name, valid_name, end, pk
        )
        if channel and role:
            await set_channel_permissions_for_role(channel, role)
        await bot.close()

    await bot.start(token)


def get_data_from_league(league):
    valid_name = discord_validation(league.name)
    color = col_dict.get(league.color, discord.Color.default())
    players = league.player.all()
    player_dIDs = [player.discordID for player in players]
    return (valid_name, league.end, league.id, color, player_dIDs)


if __name__ == "__main__":
    setup_django()
    from app.models import League

    leagues = League.objects.filter(isLive=True)
    for league in leagues:
        league_data = get_data_from_league(league)
        asyncio.run(league_process(league_data))

import os
import django
import sys

def league_decide_process():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbsl3.settings')
    django.setup()
    from app.models import Player, League
    if os.path.exists('local.py'):
        from local import DISCORD_BOT_TOKEN, GUILD_ID
        guild_id = GUILD_ID
        token = DISCORD_BOT_TOKEN
    else:
        guild_id = os.getenv('GUILD_ID')
        token = os.getenv('DISCORD_BOT_TOKEN')
    for player in Player.objects.filter(isActivated=True):
        pp = player.borderPP
        print(player, pp)
        if 1050 <= pp:
            league = League.objects.get(name="JBSL3 J1予選")
            league.player.add(player)
            continue
        # elif 800 <= pp:
        #     league = League.objects.get(name="JBSL3 J2予選")
        #     league.player.add(player)
        # else:
        #     league = League.objects.get(name="JBSL3 J3予選")
        #     league.player.add(player)


if __name__ == '__main__':
    league_decide_process()

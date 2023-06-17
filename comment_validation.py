import os
import django

def validation(s : str):
    ans = ''
    for c in s:
        # print(c.encode('utf-8'))
        if b'\xc2\x80' <= c.encode('utf-8') and c.encode('utf-8') <= b'\xd4\xbf':
            continue
        ans += c
    # print(ans)
    return ans


def process():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbsl3.settings')
    django.setup()
    from app.models import Player,Score,Participant
    for player in Player.objects.all():
        print(player.message)
        player.message = validation(player.message)
        player.save()
    for score in Score.objects.all():
        print(score.comment)
        score.comment = validation(score.comment)
        score.save()
    for participant in Participant.objects.all():
        print(participant.message)
        participant.message = validation(participant.message)
        participant.save()
        


if __name__ == '__main__':
    process()

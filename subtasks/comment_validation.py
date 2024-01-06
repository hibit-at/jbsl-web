from utils import setup_django


def rinkami_validation(s: str):
    # りんかみさんが使っていた縦に伸びる謎文字を禁止するための臨時処理
    ans = ""
    for c in s:
        # print(c.encode('utf-8'))
        if b"\xc2\x80" <= c.encode("utf-8") and c.encode("utf-8") <= b"\xd4\xbf":
            continue
        ans += c
    # print(ans)
    return ans


def process():
    from app.models import Player, Score, Participant

    for player in Player.objects.all():
        print(player.message)
        player.message = rinkami_validation(player.message)
        player.save()
    for score in Score.objects.all():
        print(score.comment)
        score.comment = rinkami_validation(score.comment)
        score.save()
    for participant in Participant.objects.all():
        print(participant.message)
        participant.message = rinkami_validation(participant.message)
        participant.save()


if __name__ == "__main__":
    setup_django()
    process()

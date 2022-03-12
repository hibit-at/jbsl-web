import os
import django


def update_process():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbsl3.settings')
    django.setup()
    from app.views import top_score_registration
    from app.models import Player, User
    from allauth.socialaccount.models import SocialAccount
    for player in Player.objects.filter(isActivated=True):
        top_score_registration(player)
        print(f'{player} updated!')
        if player.imageURL=='https://cdn.scoresaber.com/avatars/steam.png' or player.imageURL=='https://cdn.scoresaber.com/avatars/oculus.png':
            user = User.objects.get(player=player)
            social = SocialAccount.objects.get(user=user)
            print(social)
            player.imageURL = f'https://cdn.discordapp.com/avatars/{social.uid}/{social.extra_data["avatar"]}'
            player.save()


if __name__ == '__main__':
    update_process()
import os
import django


def process():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jbsl3.settings')
    django.setup()
    from app.models import Song
    for song in Song.objects.all():
        song.hash = song.hash.upper()
        song.save()
        


if __name__ == '__main__':
    process()

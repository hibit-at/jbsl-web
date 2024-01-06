import os

import django

from utils import setup_django


def process():
    from app.models import Song

    for song in Song.objects.all():
        song.hash = song.hash.upper()
        song.save()


if __name__ == "__main__":
    setup_django()
    process()

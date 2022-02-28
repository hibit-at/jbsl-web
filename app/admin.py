from django.contrib import admin
from app.models import Player, Playlist, Song, League, Score

# Register your models here.

admin.site.register(Player)
admin.site.register(Song)
admin.site.register(League)
admin.site.register(Score)
admin.site.register(Playlist)
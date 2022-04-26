from django.contrib import admin
from app.models import Player, Playlist, Song, League, Score, LeagueComment, Headline, SongInfo

class ScoreQuestion(admin.ModelAdmin):
    search_fields = ['player__name','song__title']

# Register your models here.

admin.site.register(Player)
admin.site.register(Song)
admin.site.register(League)
admin.site.register(Score, ScoreQuestion)
admin.site.register(Playlist)
admin.site.register(LeagueComment)
admin.site.register(Headline)
admin.site.register(SongInfo)
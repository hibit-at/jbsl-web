from django.contrib import admin
from app.models import Player, Playlist, Song, League, Score, Participant, Headline, SongInfo, Badge, JPMap, Match, DGA
# Register your models here.


admin.site.register(Player, search_fields=['name'])
admin.site.register(Song, search_fields=['title', 'author'])
admin.site.register(League, search_fields=['name'])
admin.site.register(Score, search_fields=['player__name', 'song__title'], readonly_fields=['song'])
admin.site.register(Playlist, search_fields=['title', 'editor'])
admin.site.register(Participant, search_fields=['player__name', 'league__name'])
admin.site.register(Headline, search_fields=['player__name'], readonly_fields=['score','player'])
admin.site.register(SongInfo)
admin.site.register(Badge)
admin.site.register(JPMap, search_fields=['name', 'uploader__name'])
admin.site.register(Match)
admin.site.register(DGA)
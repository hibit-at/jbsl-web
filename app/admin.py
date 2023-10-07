from django.contrib import admin
from app.models import Player, Playlist, Song, League, Score, Participant, Headline, SongInfo, Badge, JPMap, Match, DGA
# Register your models here.

class BadgeAdmin(admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "player":
            kwargs["queryset"] = Player.objects.order_by('name')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(Player, search_fields=['name'])
admin.site.register(Song, search_fields=['title', 'author'])
# admin.site.register(League, search_fields=['name'], readonly_fields=['player','invite','virtual'])
admin.site.register(League, search_fields=['name'], readonly_fields=['invite', 'virtual'])
admin.site.register(Score, search_fields=['player__name', 'song__title'], readonly_fields=['song'])
admin.site.register(Playlist, search_fields=['title', 'editor'], readonly_fields=['songs','recommend','CoEditor'])
admin.site.register(Participant, search_fields=['player__name', 'league__name'])
admin.site.register(Headline, search_fields=['player__name'], readonly_fields=['score','player'])
admin.site.register(SongInfo, readonly_fields=['song','playlist'], search_fields=['song__title'])
admin.site.register(Badge, BadgeAdmin)
admin.site.register(JPMap, search_fields=['name', 'uploader__name'], ordering=['-createdAt'])
admin.site.register(Match)
admin.site.register(DGA)
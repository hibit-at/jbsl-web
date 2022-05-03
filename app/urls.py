from django.urls import path, include
from . import views

app_name = 'app'

urlpatterns = [
    path('', views.index, name='index'),
    path('', include('django.contrib.auth.urls')),
    path('mypage/', views.mypage, name='mypage'),
    path('userpage/<int:sid>', views.userpage, name='userpage'),
    path('activate_process/', views.activate_process, name='activate_process'),
    path('song/<int:lid>', views.song, name='song'),
    path('create_playlist/', views.create_playlist, name='create_playlist'),
    path('playlists/', views.playlists, name='playlists'),
    path('playlist/<int:pk>', views.playlist, name='playlist'),
    path('download_playlist/<int:pk>',
         views.download_playlist, name='download_playlist'),
    path('leagues/', views.leagues, name='leagues'),
    path('leaderboard/<int:pk>', views.leaderboard, name='leaderboard'),
    path('create_league',views.create_league, name='create_league'),
    path('virtual_league/<int:pk>',views.virtual_league, name='virtual_league'),
    path('userpage/rival', views.rivalpage, name='rivalpage'),
    path('headlines/<int:page>', views.headlines, name='headlines'),
    path('players/',views.players, name='players'),
    path('debug/',views.debug, name='debug'),
    path('leaderboard/api/<int:pk>',views.api_leaderboard, name='api_leaderboard'),
]

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
    path('recalculation/', views.recalculation, name='recalculation'),
    path('suicuide/', views.suicuide, name='suicuide'),
    path('create_playlist/', views.create_playlist, name='create_playlist'),
    path('playlists/', views.playlists, name='playlists'),
    path('playlist/<slug:title>', views.playlist, name='playlist'),
    path('download_playlist/<slug:title>',
         views.download_playlist, name='download_playlist'),
]

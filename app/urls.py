from django.urls import include, path

from . import api_views, views

app_name = "app"

urlpatterns = [
    path("", views.index, name="index"),
    path("", include("django.contrib.auth.urls")),
    path("archive/", views.archive, name="archive"),
    path("activate_process/", views.activate_process, name="activate_process"),
    path("bsr_checker/", views.bsr_checker, name="bsr_checker"),
    path("create_playlist/", views.create_playlist, name="create_playlist"),
    path("create_league", views.create_league, name="create_league"),
    path(
        "download_playlist/<int:pk>", views.download_playlist, name="download_playlist"
    ),
    path("genre_criteria", views.genre_criteria, name="genre_criteria"),
    path("headlines/<int:page>", views.headlines, name="headlines"),
    path("info/<int:pk>", views.info, name="info"),
    path("koharu_graph/<int:pk>", views.koharu_graph, name="koharu_graph"),
    path("leagues/", views.leagues, name="leagues"),
    path("leaderboard/<int:pk>", views.leaderboard, name="leaderboard"),
    path("match/<int:pk>", views.match, name="match"),
    path("mypage/", views.mypage, name="mypage"),
    path("league_comment/", views.league_comment, name="league_comment"),
    path("league_edit/<int:pk>", views.league_edit, name="league_edit"),
    path("owner_comment/", views.owner_comment, name="owner_comment"),
    path("playlists/", views.playlists, name="playlists", kwargs={"page": 1}),
    path("playlists/<int:page>", views.playlists, name="playlists"),
    path("playlist/<int:pk>", views.playlist, name="playlist"),
    path("players/", views.players, name="players"),
    path("playlist_archives", views.playlist_archives, name="playlist_archive"),
    path("player_matrix/", views.player_matrix, name="player_matrix"),
    path("score_comment/", views.score_comment, name="score_comment"),
    path(
        "short_leaderboard/<int:pk>", views.short_leaderboard, name="short_leaderboard"
    ),
    path(
        "song_leaderboard/<int:league_pk>/<int:song_pk>",
        views.song_leaderboard,
        name="song_leaderboard",
    ),
    path("userpage/<int:sid>", views.userpage, name="userpage"),
    path("userpage/rival", views.rivalpage, name="rivalpage"),
    path("virtual_league/<int:pk>", views.virtual_league, name="virtual_league"),
    # api
    path("api/active_league", api_views.api_active_league, name="api_active_league"),
    path("api/dga", api_views.api_dga, name="api_dga"),
    path("api/dga/post", api_views.api_dga_post, name="api_dga_post"),
    path("api/playlist_songs/<int:pk>", api_views.api_song_info, name="api_song_info"),
    path("api/playlist/<int:pk>", api_views.api_playlist, name="api_playlist"),
    path("leaderboard/api/<int:pk>", api_views.api_leaderboard, name="api_leaderboard"),
    path("match/api/<int:pk>", api_views.api_match, name="api_match"),
]

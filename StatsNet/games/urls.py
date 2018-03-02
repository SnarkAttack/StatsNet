from django.conf.urls import url

from games.views.GameLogger import GameLogger, record_game, GameLoggerFullText
from games.views.StatsViewer import StatsViewer
from games.views import views

app_name = 'games'
urlpatterns = [
    url(r'^$', views.list_games, name='list_games'),
    url(r'^record/$', record_game, name='record_game'),
    url(r'^log/$', GameLogger.as_view(), name='log_game'),
    url(r'^log_full_game/$', GameLoggerFullText.as_view(), name='log_full_game'),
    url(r'^(?P<game_id>[0-9]+)/$', views.view_game, name='view_game'),
    url(r'^update-ids/$', views.get_ids, name='update_ids'),
    url(r'^stats/$', StatsViewer.as_view(), name='view_stats'),
    url(r'^usernames/$', views.usernames, name='usernames'),
    url(r'^register_username/$', views.register_username, name='register_username')
]

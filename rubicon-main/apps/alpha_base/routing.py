from django.urls import re_path
from alpha.settings import API_URL_PREFIX

from apps.alpha_base.__function.channels_consumer import ChannelsConsumer

websocket_urlpatterns = [
    re_path(API_URL_PREFIX + r'api/ws/channel/(?P<channel_id>\w+)/$', ChannelsConsumer.as_asgi()),
]
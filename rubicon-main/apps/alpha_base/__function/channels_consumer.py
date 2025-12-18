# channel/consumers.py
import json
from icecream import ic
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer


# from .models import Room
# from channels.generic.websocket import AsyncWebsocketConsumer

class ChannelsConsumer(WebsocketConsumer):

    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.channel_id = None
        self.channel_group_name = None
        self.channel = None

    def connect(self):
        # ic('connect', self.scope['url_route']['kwargs']['channel_id'])
        self.channel_id = self.scope['url_route']['kwargs']['channel_id']
        self.channel_group_name = 'channel_%s' % self.channel_id
        # self.room = Room.objects.get(name=self.room_name)

        # ic(self.channel_group_name)
        self.accept()
        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.channel_group_name,
            self.channel_name
        )

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.channel_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.channel_group_name,
            {
                'type': 'channel_message',
                'message': message
            }
        )

    # Receive message from room group
    def channel_message(self, event):
        message = event['message']

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            'message': message
        }))

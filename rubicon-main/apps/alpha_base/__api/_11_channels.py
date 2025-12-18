import json
import traceback
from icecream import ic

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

# def proxyAction(request_dict):
#     if request_dict['action'] == 'SEND_MESSAGE':
#         return __send_message(request_dict)
#     else:
#         return 'unsupported action'

def sendMessage (request_dict):
    channel_id = request_dict['query']['channelID']
    message = request_dict['query']['message']

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send) (
            'channel_%(channel_id)s' %{'channel_id': channel_id},
            {
                'type': 'channel_message',
                'message': message
            }
        )

    return True, None, None, None


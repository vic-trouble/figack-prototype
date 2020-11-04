import json

import util


class Codec:
    def __init__(self):
        self._types = {}
        self._rev = {}

    def register(self, message_class, id=None):
        id = id or str(message_class)
        self._types[id] = message_class
        self._rev[message_class] = id

    def encode(self, message):
        return bytes(json.dumps({'message': self._rev[type(message)], 'data': message.__dict__}), encoding='utf-8')

    def decode(self, code):
        obj = json.loads(code.decode('utf-8'))
        message = self._types[obj['message']]()
        util.object_update_from(message, obj['data'])
        return message

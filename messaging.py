import json

import util


class Codec:
    def __init__(self, auto_register=False, globals={}):
        self._types = {}
        self._rev = {}
        self._auto_register = auto_register
        self._globals = globals

    def register(self, message_class, id=None):
        id = id or str(message_class)
        self._types[id] = message_class
        self._rev[message_class] = id

    def _encode(self, obj):
        if obj is None or isinstance(obj, (int, float, bool, str)):
            return obj
        elif isinstance(obj, list):
            return [self._encode(v) for v in obj]
        elif isinstance(obj, dict):
            return {self._encode_key(k): self._encode(v) for k, v in obj.items()}
        else:
            obj_type = type(obj)
            if obj_type not in self._types and self._auto_register:
                self.register(obj_type, id=obj_type.__name__)
            return {'__message': self._rev[obj_type], '__data': self._encode(obj.__dict__)}

    def encode(self, message):
        return json.dumps(self._encode(message))

    def _decode(self, obj):
        if obj is None or isinstance(obj, (int, float, bool, str)):
            return obj
        elif isinstance(obj, list):
            return [self._decode(v) for v in obj]
        else:
            if '__message' in obj:
                obj_type = obj['__message']
                if obj_type not in self._types and self._auto_register:
                    self.register(self._globals[obj_type], id=obj_type)
                message = self._types[obj['__message']]()
                util.object_update_from(message, self._decode(obj['__data']))
                return message
            else:
                return {self._decode_key(k): self._decode(v) for k, v in obj.items()}

    def decode(self, code):
        obj = json.loads(code)
        return self._decode(obj)

    def _encode_key(self, key):
        if isinstance(key, int):
            return '_i' + str(key)
        elif isinstance(key, str):
            return key
        else:
            raise ValueError()

    def _decode_key(self, ekey):
        if ekey.startswith('_i'):
            return int(ekey[2:])
        else:
            return ekey

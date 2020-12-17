from messaging import *


class UserVal:
    def __init__(self, data=0):
        self.data = data

    def __eq__(self, user_val):
        return self.data == user_val.data


def test_codec():
    # arrange
    class MyMessage:
        def __init__(self, ival=0, sval='', aval=None, dval=None, uval=None):
            self.ival = ival
            self.sval = sval
            self.aval = aval or []
            self.dval = dval or {}
            self.uval = uval or UserVal()

        def __eq__(self, message):
            return self.__dict__ == message.__dict__

    codec = Codec()
    codec.register(MyMessage)
    codec.register(UserVal)

    message = MyMessage(ival=13, sval='something', aval=[1, 2, 3], dval={'a': 'abc', 'z': 'zyx'}, uval=UserVal())

    # act
    code = codec.encode(message)
    assert isinstance(code, str)

    decoded = codec.decode(code)
    assert isinstance(decoded, MyMessage)
    assert decoded == message


def test_int_key_in_json():
    # arrange
    codec = Codec()

    # act
    message = {1: 2}
    code = codec.encode(message)

    # assert
    decoded = codec.decode(code)
    assert decoded == message


def test_auto_register():
    # arrange
    codec = Codec(auto_register=True)

    # act
    code = codec.encode(UserVal(42))

    # assert
    codec2 = Codec(auto_register=True, globals=globals())
    decoded = codec2.decode(code)
    assert isinstance(decoded, UserVal)
    assert decoded.data == 42

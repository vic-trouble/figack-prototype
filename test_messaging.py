from messaging import *


def test_codec():
    # arrange
    class MyMessage:
        def __init__(self, ival=0, sval='', aval=None, dval=None):
            self.ival = ival
            self.sval = sval
            self.aval = aval or []
            self.dval = dval or {}

        def __eq__(self, message):
            return self.__dict__ == message.__dict__

    codec = Codec()
    codec.register(MyMessage)

    message = MyMessage(ival=13, sval='something', aval=[1, 2, 3], dval={'a': 'abc', 'z': 'zyx'})

    # act
    code = codec.encode(message)
    assert isinstance(code, bytes)

    decoded = codec.decode(code)
    assert isinstance(decoded, MyMessage)
    assert decoded == message

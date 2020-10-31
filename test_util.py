from util import *


def test_object_update_from():
    class MyClass:
        def __init__(self, val):
            self.val = val

    source = MyClass(13)
    dest = MyClass(42)
    dest_id = id(dest)

    object_update_from(dest, source)
    assert dest.val == 13
    assert id(dest) == dest_id

    object_update_from(dest, {'val': 43})
    assert dest.val == 43
    assert id(dest) == dest_id

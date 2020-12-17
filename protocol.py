from model import *


class CreateGameRequest:
    def __init__(self, player_name=None):
        self.player_name = player_name


class CreateGameResponse:
    def __init__(self, game_id=None, player_id=None):
        self.game_id = game_id
        self.player_id = player_id


class JoinGameRequest:
    def __init__(self, game_id=None, player_name=None):
        self.game_id = game_id
        self.player_name = player_name


class JoinGameResponse:
    def __init__(self, player_id=None):
        self.player_id = player_id


class GetGameRequest:
    def __init__(self, game_id=None, player_id=None):
        self.game_id = game_id
        self.player_id = player_id


class GetGameResponse:
    def __init__(self, game=None):
        self.game = game


class MoveCharRequest:
    def __init__(self, game_id=None, player_id=None, unit_id=None, x=None, y=None):
        self.game_id = game_id
        self.player_id = player_id
        self.unit_id = unit_id
        self.x = x
        self.y = y


class AttackRequest:
    def __init__(self, game_id=None, player_id=None, unit_id=None, x=None, y=None):
        self.game_id = game_id
        self.player_id = player_id
        self.unit_id = unit_id
        self.x = x
        self.y = y


class OpenRequest:
    def __init__(self, game_id=None, player_id=None, unit_id=None, x=None, y=None):
        self.game_id = game_id
        self.player_id = player_id
        self.unit_id = unit_id
        self.x = x
        self.y = y


class FireRequest:
    def __init__(self, game_id=None, player_id=None, unit_id=None, x=None, y=None):
        self.game_id = game_id
        self.player_id = player_id
        self.unit_id = unit_id
        self.x = x
        self.y = y


class PingRequest:
    def __init__(self):
        pass


class PingResponse:
    def __init__(self, server_time=None):
        self.server_time = server_time


class JumpRequest:
    def __init__(self, game_id=None, player_id=None, unit_id=None, x=None, y=None):
        self.game_id = game_id
        self.player_id = player_id
        self.unit_id = unit_id
        self.x = x
        self.y = y

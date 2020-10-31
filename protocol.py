from model import *


class CreateGameRequest:
    def __init__(self, player_name):
        self.player_name = player_name


class CreateGameResponse:
    def __init__(self, game_token, player_id):
        self.game_token = game_token
        self.player_id = player_id


class JoinGameRequest:
    def __init__(self, game_token, player_name):
        self.game_token = game_token
        self.player_name = player_name


class JoinGameResponse:
    def __init__(self, player_id):
        self.player_id = player_id


class GetGameRequest:
    def __init__(self, game_token):
        self.game_token = game_token


class GetGameResponse:
    def __init__(self, game: Game):
        self.game = game

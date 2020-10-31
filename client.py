from ops import *
from protocol import *


class Client:
    def __init__(self, server):
        self.server = server
        self.game = None
        self.game_token = None
        self.player_id = None

    def create_game(self, player_name):
        response = self.server.serve(CreateGameRequest(player_name))
        self.game_token = response.game_token
        self.player_id = response.player_id
        self._fetch_game()

    def _fetch_game(self):
        response = self.server.serve(GetGameRequest(self.game_token, self.player_id))
        if not self.game:
            self.game = response.game
        else:
            GameOp(self.game).update_from(response.game)

    def join_game(self, game_token, player_name):
        response = self.server.serve(JoinGameRequest(game_token, player_name))
        self.game_token = game_token
        self.player_id = response.player_id
        self._fetch_game()

    def move_char(self, unit_id, x, y):
        self.server.serve(MoveCharRequest(self.game_token, self.player_id, unit_id, x, y))
        self._fetch_game()

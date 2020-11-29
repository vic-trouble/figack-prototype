from connection import *
from ops import *
from protocol import *


class Client:
    def __init__(self, game_id, player_id, connection: Connection):
        self.connection = connection
        self.game = None
        self.game_id = game_id
        self.player_id = player_id
        self.fetch_count = 0

    #def create_game(self, player_name):
    #    response = self.server.serve(CreateGameRequest(player_name))
    #    self.game_id = response.game_id
    #    self.player_id = response.player_id
    #    self._fetch_game()

    def fetch_game(self):
        self.connection.outgoing.append(GetGameRequest(self.game_id, self.player_id))

    def handle(self, message):
        if isinstance(message, GetGameResponse):
            if not self.game:
                self.game = message.game
            else:
                GameOp(self.game).update_from(message.game)
            self.fetch_count += 1

    def process_connection(self):
        while self.connection.incoming:
            message = self.connection.incoming.pop(0)
            self.handle(message)

    #def join_game(self, game_id, player_name):
    #    response = self.server.serve(JoinGameRequest(game_id, player_name))
    #    self.game_id = game_id
    #    self.player_id = response.player_id
    #    self._fetch_game()

    def move_char(self, unit_id, x, y):
        self.connection.outgoing.append(MoveCharRequest(self.game_id, self.player_id, unit_id, x, y))
        self.fetch_game()

    @property
    def char(self):
        return next(iter(self.game.units_by_player[self.player_id]))

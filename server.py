import threading

from model import *
from ops import *
from protocol import *


PLAYER_CHAR_INIT_HP = 10


class Server:
    def __init__(self):
        self._games = []
        self._lock = threading.Lock()

    def serve(self, request):
        with self._lock:
            if isinstance(request, CreateGameRequest):
                game = self._create_game()
                self._games.append(game)
                game_token = len(self._games)

                player = GameOp(game).add_player(request.player_name)
                GameOp(game).spawn_unit(hp=PLAYER_CHAR_INIT_HP, player_id=player.id)

                return CreateGameResponse(game_token, player.id)
            
            elif isinstance(request, GetGameRequest):
                return GetGameResponse(self._get_game(request.game_token))
            
            elif isinstance(request, JoinGameRequest):
                game = self._get_game(request.game_token)
                player = GameOp(game).add_player(request.player_name)
                GameOp(game).spawn_unit(hp=PLAYER_CHAR_INIT_HP, player_id=player.id)
                return JoinGameResponse(player.id)

            else:
                raise RuntimeError('Unknown request %s', type(request))

    def _create_game(self):
        game = Game()
        GameOp(game).init()
        return game

    def _get_game(self, game_token):
        return self._games[game_token - 1]
from collections import defaultdict
import logging
import threading

from connection import *
from model import *
from ops import *
from protocol import *


PLAYER_CHAR_INIT_HP = 10
PLAYER_CHAR_INIT_DAMAGE = 2

logging.basicConfig(level=logging.DEBUG)


class Server:
    def __init__(self):
        self._games = {}
        self._lock = threading.RLock()
        self._connections = {}
        self._next_game_id = 1

    def connect(self, game_id, player_id): #, auth_token):
        with self._lock:
            logging.debug('self._games = %s', self._games)
            assert game_id in self._games
            assert player_id in self._games[game_id].players
            conn_key = (game_id, player_id)
            assert conn_key not in self._connections
            conn = Connection()
            self._connections[conn_key] = conn
            return conn

    def get_connection(self, game_id, player_id):
        with self._lock:
            conn_key = (game_id, player_id)
            return self._connections.get(conn_key)

    def get_connections(self, game_id):
        with self._lock:
            return list(conn for conn_key, conn in self._connections.items() if conn_key[0] == game_id)

    def get_game(self, game_id):
        with self._lock:
            return self._games[game_id]

    def process_connections(self):
        with self._lock:
            for conn in self._connections.values():
                while conn.incoming:
                    request = conn.incoming.pop(0)
                    response = self.serve(request)
                    if response:
                        conn.outgoing.append(response)

    def serve(self, request):
        with self._lock:
            try:
                if isinstance(request, CreateGameRequest):
                    game = self._create_game()

                    player = GameOp(game).add_player(request.player_name)
                    GameOp(game).spawn_unit(Unit(hp=PLAYER_CHAR_INIT_HP, damage=PLAYER_CHAR_INIT_DAMAGE, player_id=player.id))

                    game_id = self._next_game_id
                    self._next_game_id += 1
                    self._games[game_id] = game

                    logging.debug('self._games = %s', self._games)

                    return CreateGameResponse(game_id, player.id)

                elif isinstance(request, GetGameRequest):
                    return GetGameResponse(self._games[request.game_id])

                elif isinstance(request, JoinGameRequest):
                    game = self._games[request.game_id]
                    player = GameOp(game).add_player(request.player_name)
                    GameOp(game).spawn_unit(Unit(hp=PLAYER_CHAR_INIT_HP, damage=PLAYER_CHAR_INIT_DAMAGE, player_id=player.id))
                    return JoinGameResponse(player.id)

                elif isinstance(request, MoveCharRequest):
                    game = self._games[request.game_id]
                    char = game.entities[request.unit_id]
                    assert abs(char.x - request.x) <= 1 and abs(char.y - request.y) <= 1
                    assert (request.x, request.y) in game.maze.free_cells - game.occupied_cells
                    EntityOp(char).move(request.x, request.y)

                elif isinstance(request, AttackRequest):
                    game = self._games[request.game_id]
                    char = game.entities[request.unit_id]
                    assert abs(char.x - request.x) <= 1 and abs(char.y - request.y) <= 1
                    target = next(unit for unit in game.units if (unit.x, unit.y) == (request.x, request.y))
                    UnitOp(target).take_damage(char.damage, game.tick)
                    if target.dead:
                        GameOp(game).add_entity(Grave(x=target.x, y=target.y))
                        GameOp(game).remove_entity(target)

                elif isinstance(request, OpenRequest):
                    game = self._games[request.game_id]
                    char = game.entities[request.unit_id]
                    assert abs(char.x - request.x) <= 1 and abs(char.y - request.y) <= 1
                    assert game.maze.get(request.x, request.y) == '+'
                    MazeOp(game.maze).open_door(request.x, request.y)

                else:
                    raise RuntimeError('Unknown request %s', type(request))

            except Exception as e:
                logging.exception(e)

    def _create_game(self):
        game = Game()
        GameOp(game).init()
        return game

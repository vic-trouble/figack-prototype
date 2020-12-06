from copy import deepcopy
import random

from model import *
from util import *


class GameOp:
    def __init__(self, game):
        self._game = game

    def add_player(self, player_name):
        player = Player(len(self._game.players) + 1, player_name)
        self._game.players[player.id] = player
        return player

    def init(self):
        width = random.randint(10, 20)
        height = random.randint(5, 15)
        self._game.maze = Maze(width, height)
        for y in range(height):
            for x in range(width):
                if y in (0, height - 1):
                    cell = '-'
                elif x in (0, width - 1):
                    cell = '|'
                else:
                    cell = '.'
                self._game.maze.set(x, y, cell)

    def spawn_unit(self, hp=1, player_id=0):
        pos = random.choice(list(self._game.maze.free_cells - self._game.occupied_cells))
        unit_id = len(self._game.entities) + 1
        unit = Unit(unit_id, pos[0], pos[1], hp=hp, player_id=player_id)
        self._game.entities[unit_id] = unit

    def update_from(self, game):
        def update_dict(dest, source, op_class):
            # existing
            removed = []
            for id, thing in dest.items():
                if id in source:
                    op_class(thing).update_from(source[id])
                else:
                    removed.append(id)

            # new
            for id in set(source.keys()) - set(dest.keys()):
                dest[id] = source[id]

            # removed
            for id in removed:
                del dest[id]

        MazeOp(self._game.maze).update_from(game.maze)
        update_dict(self._game.players, game.players, PlayerOp)
        update_dict(self._game.entities, game.entities, EntityOp)


class EntityOp:
    def __init__(self, entity):
        self._entity = entity

    def move(self, x, y):
        self._entity.x = x
        self._entity.y = y

    def update_from(self, entity):
        object_update_from(self._entity, entity)


class PlayerOp:
    def __init__(self, player):
        self._player = player

    def update_from(self, player):
        object_update_from(self._player, player)


class MazeOp:
    def __init__(self, maze):
        self._maze = maze

    def update_from(self, maze):
        object_update_from(self._maze, maze)

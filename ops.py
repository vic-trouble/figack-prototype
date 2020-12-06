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

    def spawn_unit(self, unit):
        pos = random.choice(list(self._game.maze.free_cells - self._game.occupied_cells))
        unit.x = pos[0]
        unit.y = pos[1]
        self.add_entity(unit)

    def add_entity(self, entity):
        entity.id = self._game.issue_entity_id()
        self._game.entities[entity.id] = entity

    def remove_entity(self, entity):
        del self._game.entities[entity.id]

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


class UnitOp:
    def __init__(self, unit):
        self._unit = unit

    def take_damage(self, damage):
        self._unit.hp = max(self._unit.hp - damage, 0)

    def update_from(self, unit):
        object_update_from(self._unit, unit)


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

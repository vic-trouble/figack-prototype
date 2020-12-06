from copy import deepcopy
import logging
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
        height = random.randint(10, 15)
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

        def split(start_x, start_y, width, height, horz=True, depth=1):
            if not depth:
                return

            if horz:
                if height < 5 or width < 3:
                    return

                # split
                split_y = random.randint(2, height - 3)
                for x in range(width):
                    self._game.maze.set(start_x + x, start_y + split_y, '-')

                # add a door
                door_x = random.randint(1, width - 2)
                self._game.maze.set(start_x + door_x, start_y + split_y, '+')

                # subsplit
                if door_x < width // 2:
                    subsplit_x = door_x + 1
                    subwidth = width - subsplit_x
                else:
                    subsplit_x = start_x
                    subwidth = door_x - 1 - subsplit_x

                if split_y < height // 2:
                    subsplit_y = split_y
                    subheight = height - subsplit_y
                else:
                    subsplit_y = start_y
                    subheight = split_y - start_y
                split(subsplit_x, subsplit_y, subwidth, subheight, not horz, depth-1)

            else:
                if width < 5 or height < 3:
                    return

                # split
                split_x = random.randint(2, width - 3)
                for y in range(height):
                    self._game.maze.set(start_x + split_x, start_y + y, '|')

                # add a door
                door_y = random.randint(1, height - 2)
                self._game.maze.set(start_x + split_x, start_y + door_y, '+')

                # subsplit
                if door_y < height // 2:
                    subsplit_y = door_y + 1
                    subheight = height - subsplit_y
                else:
                    subsplit_y = start_y
                    subheight = door_y - 1 - subsplit_y

                if split_x < width // 2:
                    subsplit_x = split_x
                    subwidth = width - subsplit_x
                else:
                    subsplit_x = start_x
                    subwidth = split_x - start_x
                split(subsplit_x, subsplit_y, subwidth, subheight, not horz, depth-1)

        split(0, 0, width, height, horz=bool(random.randint(0, 1)), depth=random.randint(1, 3))

        # add random obstacles
        for i in range(random.randint(0, 5)):
            x = random.randint(1, width - 2)
            y = random.randint(1, height - 2)
            for delta in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                if self._game.maze.get(x + delta[0], y + delta[1]) != '.':
                    break
            else:
                self._game.maze.set(x, y, '-')

        logging.debug('generated maze: \n%s', '\n'.join(''.join(row) for row in self._game.maze.map))

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

    def open_door(self, x, y):
        self._maze.set(x, y, '.')

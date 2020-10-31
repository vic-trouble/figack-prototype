from copy import deepcopy
import random

from model import *


class GameOp:
    def __init__(self, game):
        self._game = game

    def add_player(self, player_name):
        player = Player(len(self._game.players) + 1, player_name)
        self._game.players[player.id] = player
        return player

    def init(self):
        width = random.randint(10, 40)
        height = random.randint(5, 25)
        self._game.maze = Maze(width, height)
        for y in range(height):
            for x in range(width):
                if y in (0, height - 1):
                    cell = '|'
                elif x in (0, width - 1):
                    cell = '-'
                else:
                    cell = '.'
                self._game.maze.set(x, y, cell)

    def spawn_unit(self, hp=1, player_id=0):
        maze = deepcopy(self._game.maze)
        for e in self._game.entities:
            if isinstance(e, Unit):
                maze.set(e.x, e.y, '?')
        pos = random.choice(maze.free_cells)
        unit_id = len(self._game.entities) + 1
        unit = Unit(unit_id, pos[0], pos[1], hp=hp, player_id=player_id)
        self._game.entities[unit_id] = unit

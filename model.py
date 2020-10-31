from collections import defaultdict


class Maze:
    def __init__(self, width=0, height=0, map=None):
        if map:
            self.map = map
        else:
            assert width and height
            self.map = [[' ' for _ in range(width)] for _ in range(height)]

    @property
    def height(self):
        return len(self.map)

    @property
    def width(self):
        return len(self.map[0])

    def get(self, x, y):
        return self.map[y][x]

    def set(self, x, y, v):
        self.map[y][x] = v

    @property
    def free_cells(self):
        return [(x, y) for x in range(self.width) for y in range(self.height) if self.get(x, y) == '.']


class MazeEntity:
    def __init__(self, id: int, x: int, y: int):
        self.id = id
        self.x = x
        self.y = y


class Unit(MazeEntity):
    def __init__(self, id, x, y, hp=0, player_id=0):
        super().__init__(id, x, y)
        self.hp = hp
        self.player_id = player_id


class Player:
    def __init__(self, id, name):
        self.id = id
        self.name = name


class Game:
    def __init__(self, maze=None, entities=None, players=None):
        self.maze = maze
        self.entities = entities or {}
        self.players = players or {}

    @property
    def units_by_player(self):
        r = defaultdict(list)
        for entity in self.entities.values():
            if isinstance(entity, Unit) and entity.player_id:
                r[entity.player_id].append(entity)
        return r

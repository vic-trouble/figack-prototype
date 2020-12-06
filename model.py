from collections import defaultdict


class Maze:
    def __init__(self, width=0, height=0, map=None):
        if map:
            self.map = map
        else:
            # assert width and height
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
        return set((x, y) for x in range(self.width) for y in range(self.height) if self.get(x, y) == '.')


class MazeEntity:
    def __init__(self, id=0, x=0, y=0, opaque=False):
        self.id = id
        self.x = x
        self.y = y
        self.opaque = opaque


class Grave(MazeEntity):
    def __init__(self, id=0, x=0, y=0):
        super().__init__(id=id, x=x, y=y)


class Unit(MazeEntity):
    def __init__(self, id=0, x=0, y=0, hp=0, damage=0, player_id=0):
        super().__init__(id=id, x=x, y=y, opaque=True)
        self.hp = hp
        self.damage = damage
        self.player_id = player_id

    @property
    def dead(self):
        return self.hp <= 0


class Player:
    def __init__(self, id=0, name=''):
        self.id = id
        self.name = name


class Game:
    def __init__(self, maze=None, entities=None, players=None):
        self.maze = maze
        self.entities = entities or {}
        self.players = players or {}
        self.next_entity_id = 1

    def issue_entity_id(self):
        entity_id = self.next_entity_id
        self.next_entity_id += 1
        return entity_id

    @property
    def units_by_player(self):
        r = defaultdict(list)
        for unit in self.units:
            if unit.player_id:
                r[unit.player_id].append(unit)
        return r

    @property
    def units(self):
        yield from (entity for entity in self.entities.values() if isinstance(entity, Unit))

    @property
    def occupied_cells(self):
        return set((entity.x, entity.y) for entity in self.entities.values() if entity.opaque)

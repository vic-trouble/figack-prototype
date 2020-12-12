from collections import defaultdict


class Maze:
    def __init__(self, width=0, height=0, map=None):
        if map:
            self.map = map
        else:
            # assert width and height
            self.map = [[' '] * width for _ in range(height)]

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


class Effects:
    def __init__(self, hit_tick=None):
        self.hit_tick = hit_tick


LEFT, RIGHT, UP, DOWN = range(4)


class MazeEntity:
    def __init__(self, id=0, x=0, y=0, opaque=False, effects=None, direction=LEFT):
        self.id = id
        self.x = x
        self.y = y
        self.opaque = opaque
        self.effects = effects or Effects()
        self.direction = direction


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


class Projectile(MazeEntity):
    def __init__(self, damage=0, speed=0, start_x=0, start_y=0, target_x=0, target_y=0, start_time=0):
        super().__init__(x=start_x, y=start_y)
        self.damage = damage
        self.speed = speed
        self.start_x = start_x
        self.start_y = start_y
        self.target_x = target_x
        self.target_y = target_y
        self.start_time = start_time
        if target_x < start_x:
            self.direction = LEFT
        elif target_x > start_x:
            self.direction = RIGHT
        elif target_y < start_y:
            self.direction = UP
        elif target_y > start_y:
            self.direction = DOWN


class Player:
    def __init__(self, id=0, name=''):
        self.id = id
        self.name = name


class Game:
    def __init__(self, maze=None, entities=None, players=None, tick=1):
        self.maze = maze
        self.entities = entities or {}
        self.players = players or {}
        self.next_entity_id = 1
        self.tick = tick
        self.visibility = {}

    def next_tick(self):
        self.tick += 1

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

    def get_visibility(self, player_id, x, y):
        return self.visibility[player_id][y][x]  # NOTE: weird keying because of json

    def set_visibility(self, player_id, x, y, v):
        self.visibility[player_id][y][x] = v

from copy import deepcopy
import logging
import math
import random

from model import *
from util import *


VISIBILITY_RADIUS = 10


class GameOp:
    def __init__(self, game):
        self._game = game

    def add_player(self, player_name):
        player = Player(len(self._game.players) + 1, player_name)
        self._game.players[player.id] = player
        self._game.visibility[player.id] = [[0] * self._game.maze.width for _ in range(self._game.maze.height)] # 0..1
        return player

    def init(self):
        width = random.randint(10, 20)
        height = random.randint(10, 15)
        self._game.maze = Maze(width, height)

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
        class dict_proxy:
            def __init__(self, d):
                self.d = d

            def update_from(self, other):
                self.d.update(other)

        class list_proxy:
            def __init__(self, l):
                self.l = l

            def update_from(self, other):
                self.l.clear()
                self.l.extend(other)

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
        update_dict(self._game.visibility, game.visibility, list_proxy)

    def update_visibility(self, player_id, x, y):
        for my in range(self._game.maze.height):
            for mx in range(self._game.maze.width):
                dist2 = (mx - x)**2 + (my - y)**2
                r2 = VISIBILITY_RADIUS**2
                if dist2 <= r2:
                    self._game.set_visibility(player_id, mx, my, 0.5 + 0.5 * (1 - dist2/r2))
                else:
                    self._game.set_visibility(player_id, mx, my, min(self._game.get_visibility(player_id, mx, my), 0.5))

    def simulate(self, game_time):
        game_changed = False

        # move projectiles
        killed = []
        for entity in self._game.entities.values():
            if isinstance(entity, Projectile):
                arrow = entity
                if not arrow.speed:
                    continue
                ax, ay = arrow.x, arrow.y
                x, y = ProjectileOp(arrow).fly(game_time)
                while (ax, ay) != (x, y):
                    if abs(ax - x) > abs(ay - y):
                        ax += 1 if ax < x else -1
                    elif abs(ay - y) > abs(ax - x):
                        ay += 1 if ay < y else -1
                    else:
                        ax += 1 if ax < x else -1
                        ay += 1 if ay < y else -1
                    if (ax, ay) in self._game.maze.free_cells - self._game.occupied_cells:
                        EntityOp(arrow).move(ax, ay)
                        game_changed = True
                    elif (ax, ay) != (arrow.start_x, arrow.start_y):
                        target = next((unit for unit in self._game.units if (unit.x, unit.y) == (ax, ay)), False)
                        if target:
                            EntityOp(arrow).move(ax, ay)
                            UnitOp(target).take_damage(arrow.damage, self._game.tick)
                            if target.dead:
                                killed.append(target)
                        # we're at opaque cell, so stop flying anyway
                        arrow.speed = 0
                        game_changed = True
                        break

        for target in killed:
            UnitOp(target).take_damage(arrow.damage, self._game.tick)
            if target.dead: # repetition; not good
                self.add_entity(Grave(x=target.x, y=target.y))
                self.remove_entity(target)

        return game_changed


class EntityOp:
    def __init__(self, entity):
        self._entity = entity

    def move(self, x, y):
        if x < self._entity.x:
            self._entity.direction = LEFT
        elif x > self._entity.x:
            self._entity.direction = RIGHT
        elif y < self._entity.y:
            self._entity.direction = UP
        elif y > self._entity.y:
            self._entity.direction = DOWN
        self._entity.x = x
        self._entity.y = y

    def update_from(self, entity):
        object_update_from(self._entity, entity)


class UnitOp:
    def __init__(self, unit):
        self._unit = unit

    def take_damage(self, damage, tick):
        self._unit.hp = max(self._unit.hp - damage, 0)
        self._unit.effects.hit_tick = tick

    def update_from(self, unit):
        object_update_from(self._unit, unit)

    def jump(self, x, y, tick, walkable_cells):
        if x < self._unit.x:
            self._unit.direction = LEFT
        elif x > self._unit.x:
            self._unit.direction = RIGHT
        elif y < self._unit.y:
            self._unit.direction = UP
        elif y > self._unit.y:
            self._unit.direction = DOWN
        while self._unit.pos != (x, y):
            nx, ny = self._unit.x, self._unit.y
            if nx < x:
                nx += 1
            elif nx > x:
                nx -= 1
            elif ny < y:
                ny += 1
            elif ny > y:
                ny -= 1
            if (nx, ny) not in walkable_cells:
                break
            self._unit.x = nx
            self._unit.y = ny
        self._unit.effects.jump_tick = tick

    def teleport(self, x, y, tick):
        self._unit.x = x
        self._unit.y = y
        self._unit.effects.teleport_tick = tick


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

    def generate(self):
        maze = self._maze
        width = self._maze.width
        height = self._maze.height
        for y in range(height):
            for x in range(width):
                if y in (0, height - 1):
                    cell = '-'
                elif x in (0, width - 1):
                    cell = '|'
                else:
                    cell = '.'
                maze.set(x, y, cell)

        def split(start_x, start_y, width, height, horz=True, depth=1):
            if not depth:
                return

            if horz:
                if height < 5 or width < 3:
                    return

                # split
                split_y = random.randint(2, height - 3)
                for x in range(width):
                    maze.set(start_x + x, start_y + split_y, '-')

                # add a door
                door_x = random.randint(1, width - 2)
                maze.set(start_x + door_x, start_y + split_y, '+')

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
                    maze.set(start_x + split_x, start_y + y, '|')

                # add a door
                door_y = random.randint(1, height - 2)
                maze.set(start_x + split_x, start_y + door_y, '+')

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
                if maze.get(x + delta[0], y + delta[1]) != '.':
                    break
            else:
                maze.set(x, y, '-')

        logging.debug('generated maze: \n%s', '\n'.join(''.join(row) for row in maze.map))


class ProjectileOp:
    def __init__(self, projectile):
        assert isinstance(projectile, Projectile)
        self._projectile = projectile

    def update_from(self, projectile):
        object_update_from(self._projectile, projectile)

    def fly(self, game_time):
        if not self._projectile.speed:
            return (self._projectile.x, self._projectile.y)

        vx = self._projectile.target_x - self._projectile.start_x
        vy = self._projectile.target_y - self._projectile.start_y
        vv = math.hypot(vx, vy)
        vx /= vv
        vy /= vv
        x = round(self._projectile.start_x + vx * self._projectile.speed * (game_time - self._projectile.start_time))
        y = round(self._projectile.start_y + vy * self._projectile.speed * (game_time - self._projectile.start_time))
        return (x, y)

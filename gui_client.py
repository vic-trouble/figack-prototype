#! /usr/bin/python3.9

import argparse
import asyncio
import aiohttp
from collections import defaultdict
import copy
import glob
import json
import logging
import math
import os
import pygame
from pygame.locals import *
import random
from threading import Thread, Lock, Event
import time

from client import Client
from connection import Connection
from messaging import Codec
import model
import protocol


MAX_MESSAGE_FRESHNESS = 20
PING_TIMEOUT = 10
MAX_RECONNECT_BACKOFF = 120


async def read_socket(ws, codec, connection, lock, client):
    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            message = codec.decode(msg.data)
            with lock:
                connection.incoming.append(message)
                client.process_connection()
        elif msg.type == aiohttp.WSMsgType.CLOSED:
            logging.debug('Websocket closed')
            break
        elif msg.type == aiohttp.WSMsgType.ERROR:
            logging.debug('Websocket error')
            break


async def write_socket(ws, codec, connection, lock):
    while not ws.closed:
        with lock:
            while connection.outgoing:
                message = connection.outgoing.pop(0)
                await ws.send_str(codec.encode(message))
        await asyncio.sleep(0)


async def wait_stop_flag(stop_flag, ws):
    await asyncio.to_thread(stop_flag.wait)
    await ws.close()


async def check_connection(session, client, stop_flag, reconnect_flag):
    while not stop_flag.is_set():
        if client.last_ping_ts:
            if time.time() - client.last_ping_ts > PING_TIMEOUT:
                logging.debug('Connection lost')
                stop_flag.set()
                reconnect_flag.set()
        elif client.last_server_msg_ts and time.time() - client.last_server_msg_ts > MAX_MESSAGE_FRESHNESS:
            client.ping()

        await asyncio.sleep(1)


async def connect(session, client, client_lock, stop_flag, reconnect_flag):
    codec = Codec()
    for obj in ( \
            protocol.GetGameRequest, protocol.GetGameResponse, protocol.MoveCharRequest, protocol.AttackRequest, protocol.OpenRequest, \
            protocol.FireRequest, protocol.PingRequest, protocol.PingResponse, \
            model.Game, model.Player, model.Maze, model.Unit, model.Grave, model.Effects, model.Projectile):
        codec.register(obj)

    logging.debug('Connecting...')
    try:
        async with session.ws_connect(f'http://localhost:8080/connect?game_id={client.game_id}&player_id={client.player_id}') as ws:
            logging.debug('Connected')
            save_state(client, 'client.json')

            client.on_connected()

            read_task = asyncio.create_task(read_socket(ws, codec, client.connection, client_lock, client))
            write_task = asyncio.create_task(write_socket(ws, codec, client.connection, client_lock))
            wait_stop_task = asyncio.create_task(wait_stop_flag(stop_flag, ws))
            check_connection_task = asyncio.create_task(check_connection(session, client, stop_flag, reconnect_flag))
            await asyncio.gather(read_task, write_task, wait_stop_task, check_connection_task)
    except aiohttp.client_exceptions.ClientConnectionError as e:
        logging.debug('Failed to connect: %s', e)
        reconnect_flag.set()
        stop_flag.set()


def save_state(client, filename):
    with open(filename, 'w') as f:
        json.dump({'game_id': client.game_id, 'player_id': client.player_id}, f)


def load_state(filename):
    if os.path.exists(filename):
        with open(filename) as f:
            return json.load(f)


async def async_main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('--new', default=False, action='store_true')
    args = argparser.parse_args()

    game_id, player_id = None, None

    if not args.new:
        if state := load_state('client.json'):
            s = 'O'
            game_id = state['game_id']
            player_id = state['player_id']

    if game_id is None:
        s = ''
        while s not in ('C', 'J', 'O'):
            print('(C)reate, (J)oin, c(O)nnect? ', end='')
            s = input().upper()

    async with aiohttp.ClientSession() as session:
        if s == 'C':
            async with session.get('http://localhost:8080/create', params={'name': 'player1'}) as response:
                j = await response.json()
                game_id = j['game_id']
                player_id = j['player_id']
                logging.debug('Created game %s', game_id)
        elif s == 'J':
            print('Enter game_id: ', end='')
            game_id = int(input())
            async with session.get('http://localhost:8080/join', params={'name': 'player2', 'game_id': game_id}) as response:
                j = await response.json()
                player_id = j['player_id']
        elif s == 'O':
            if game_id is None:
                print('Enter game_id: ', end='')
                game_id = int(input())
            if player_id is None:
                print('Enter player_id: ', end='')
                player_id = int(input())

        # create client
        connection = Connection()
        client = Client(game_id, player_id, connection)
        client_lock = Lock()

        stop_flag = Event()
        reconnect_flag = Event()

        render_thread = Thread(target=render, args=(client, client_lock, stop_flag, reconnect_flag))
        render_thread.start()

        while True:
            await connect(session, client, client_lock, stop_flag, reconnect_flag)
            if reconnect_flag.is_set():
                stop_flag.clear()
                reconnect_flag.clear()
                logging.debug('Reconnecting in %d s', client.reconnect_backoff)
                await asyncio.sleep(client.reconnect_backoff)
                client.reconnect_backoff *= 2
                client.reconnect_backoff = min(client.reconnect_backoff, MAX_RECONNECT_BACKOFF)
            else:
                break

        stop_flag.set()
        render_thread.join()


def render(client, lock, stop_flag, reconnect_flag):
    try:
        CELL_SIZE = 48
        EFFECT_WEAR_OUT = 0.25

        SHADE = []
        RESOURCES = defaultdict(list)
        def load_resources():
            for filename in glob.glob('./art/*.png'):
                img = pygame.image.load(filename).convert_alpha()
                key = os.path.splitext(os.path.split(filename)[-1])[0]
                if '-' in key:
                    suffix = key.split('-')[-1]
                    try:
                        suffix = int(suffix)
                        key = key[:key.rfind('-')]
                    except ValueError:
                        pass
                RESOURCES[key].append(img)

            for i in range(11):
                shade = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                #pygame.draw.rect(shade, (0, 0, 0, int(255 / 11 * (11 - i))), (0, 0, CELL_SIZE, CELL_SIZE))
                shade.fill((0, 0, 0))
                shade.set_alpha(int(255 / 11 * (11 - i)))
                SHADE.append(shade.convert_alpha())

            for projectile in ('arrow', ):
                resources_projectiles[projectile] = []
                for res_img in RESOURCES[projectile]:
                    rotate = pygame.transform.rotate
                    resources_projectiles[projectile].append((res_img, rotate(res_img, 180), rotate(res_img, 270), rotate(res_img, 90)))

        # the lower, the eagerly drawn
        def draw_order(entity):
            if isinstance(entity, model.Grave):
                return 1
            elif isinstance(entity, model.Unit):
                return 10
            elif isinstance(entity, model.Projectile):
                return 20 if entity.speed else 5

        resources_map = {} # id -> img
        resources_units = {} # id -> (left_img, right_img)
        resources_projectiles = {} # id -> (left_img, right_img, up_img, down_img)
        unit_direction = defaultdict(int)
        tick_to_time = {} # tick -> time TODO: leaking here
        subtile_xy = {} # id -> (x, y, smooth_flag) subtile coordinates, for smooth animation

        screen = None

        while True:
            if not reconnect_flag.is_set() and stop_flag.is_set():
                break
            with lock:
                if not client.game:
                    continue

                now = time.time() # local timer, todo: use server time

                if not pygame.get_init():
                    pygame.init()
                    screen = pygame.display.set_mode((CELL_SIZE * client.game.maze.width, CELL_SIZE * client.game.maze.height))
                    load_resources()

                # fill background
                background = pygame.Surface(screen.get_size())
                background.fill((0, 0, 0))

                # draw maze
                maze = client.game.maze
                for y in range(maze.height):
                    for x in range(maze.width):
                        visibility = client.game.get_visibility(client.player_id, x, y)
                        if not visibility:
                            continue
                        cell = maze.get(x, y)
                        res_key = (cell, x, y)
                        if res_key not in resources_map:
                            tile = None
                            if cell == '.':
                                tile = 'floor'
                            elif cell == '+':
                                tile = 'door-closed'
                            elif cell in '-|':
                                u = y > 0 and maze.get(x, y - 1) in '-|'
                                d = y < maze.height - 1 and maze.get(x, y + 1) in '-|'
                                l = x > 0 and maze.get(x - 1, y) in '-|'
                                r = x < maze.width - 1 and maze.get(x + 1, y) in '-|'
                                tile = 'wall' + {
                                    (False, False, False, False): '',
                                    (True,  True,  False, False): '-v',
                                    (True,  False, False, False): '-u',
                                    (False, True,  False, False): '-d',
                                    (False, False, True,  True ): '-h',
                                    (False, False, True,  False): '-l',
                                    (False, False, False, True ): '-r',
                                    (True,  False, True,  False): '-dr',
                                    (True,  False, False, True ): '-dl',
                                    (False, True,  True,  False): '-ur',
                                    (False, True,  False, True ): '-ul',
                                    (True,  True,  False, True ): '-vr',
                                    (True,  True,  True,  False): '-vl',
                                    (False, True,  True,  True ): '-hd',
                                    (True,  False, True,  True ): '-hu',
                                }[(u, d, l, r)]
                            if tile:
                                assert RESOURCES[tile], tile
                                res_img = random.choice(RESOURCES[tile])
                                resources_map[res_key] = res_img
                        background.blit(resources_map[res_key], (CELL_SIZE*x, CELL_SIZE*y))

                # draw entities
                for entity in sorted(client.game.entities.values(), key=draw_order):
                    if client.game.get_visibility(client.player_id, entity.x, entity.y) > 0.5:
                        if isinstance(entity, model.Unit):
                            unit = entity
                            if unit.id not in resources_units:
                                res_index = hash((client.game_id, unit.id)) % len(RESOURCES['hero'])
                                res_img = RESOURCES['hero'][res_index]
                                resources_units[unit.id] = (res_img, pygame.transform.flip(res_img, True, False))
                            if unit.direction == model.LEFT:
                                unit_direction[unit.id] = 0
                            elif unit.direction == model.RIGHT:
                                unit_direction[unit.id] = 1
                            background.blit(resources_units[unit.id][unit_direction[unit.id]], (CELL_SIZE * unit.x, CELL_SIZE * unit.y))
                            if unit.player_id == client.player_id:
                                pygame.draw.rect(background, (0, 255, 0), (CELL_SIZE * unit.x, CELL_SIZE * unit.y, CELL_SIZE, CELL_SIZE), width=1)
                            if unit.effects.hit_tick:
                                if unit.effects.hit_tick not in tick_to_time:
                                    tick_to_time[unit.effects.hit_tick] = now
                                if now - tick_to_time[unit.effects.hit_tick] < EFFECT_WEAR_OUT:
                                    background.blit(RESOURCES['bang'][0], (CELL_SIZE * unit.x, CELL_SIZE * unit.y))
                        elif isinstance(entity, model.Grave):
                            if entity.id not in resources_units:
                                resources_units[entity.id] = random.choice(RESOURCES['bones'])
                            background.blit(resources_units[entity.id], (CELL_SIZE * entity.x, CELL_SIZE * entity.y))
                        elif isinstance(entity, model.Projectile):
                            arrow = entity
                            if arrow.id not in resources_units:
                                resources_units[arrow.id] = random.choice(resources_projectiles['arrow'])
                            if arrow.id not in subtile_xy:
                                subtile_xy[arrow.id] = (0, 0, True)
                            if arrow.speed:
                                if subtile_xy[arrow.id][2]:
                                    vx = arrow.target_x - arrow.start_x
                                    vy = arrow.target_y - arrow.start_y
                                    vv = math.hypot(vx, vy)
                                    vx /= vv
                                    vy /= vv
                                    x = round(arrow.start_x * CELL_SIZE + vx * arrow.speed * (now - arrow.start_time) * CELL_SIZE) - arrow.x * CELL_SIZE
                                    y = round(arrow.start_y * CELL_SIZE + vy * arrow.speed * (now - arrow.start_time) * CELL_SIZE) - arrow.y * CELL_SIZE
                                    tx, ty = arrow.x + round(x / CELL_SIZE), arrow.y + round(y / CELL_SIZE)
                                    if (tx, ty) == (arrow.start_x, arrow.start_y) or (tx, ty) in client.game.maze.free_cells - client.game.occupied_cells:
                                        subtile_xy[arrow.id] = (x, y, True)
                                    else:
                                        subtile_xy[arrow.id] = (subtile_xy[arrow.id][0], subtile_xy[arrow.id][1], False) # stop extrapolating
                            else:
                                subtile_xy[arrow.id] = (0, 0, False)
                            background.blit(resources_units[arrow.id][arrow.direction], (CELL_SIZE * arrow.x + subtile_xy[arrow.id][0], CELL_SIZE * arrow.y + subtile_xy[arrow.id][1]))

                # shade
                for y in range(maze.height):
                    for x in range(maze.width):
                        if visibility := client.game.get_visibility(client.player_id, x, y):
                            background.blit(SHADE[int(visibility * 10)], (CELL_SIZE*x, CELL_SIZE*y), special_flags=BLEND_ALPHA_SDL2)

                # Blit everything to the screen
                screen.blit(background, (0, 0))
                pygame.display.flip()

                inp = None
                for event in pygame.event.get():
                    if event.type == QUIT:
                        stop_flag.set()
                    elif event.type == KEYDOWN:
                        if event.key == K_DOWN:
                            inp = 'S'
                        elif event.key == K_UP:
                            inp = 'W'
                        elif event.key == K_LEFT:
                            inp = 'A'
                        elif event.key == K_RIGHT:
                            inp = 'D'
                        elif event.key == K_ESCAPE:
                            stop_flag.set()
                        elif event.key == K_SPACE:
                            if client.char:
                                delta = {
                                    model.LEFT: (-1, 0),
                                    model.UP: (0, -1),
                                    model.DOWN: (0, 1),
                                    model.RIGHT: (1, 0)
                                }
                                client.fire(client.char.id, client.char.x + delta[client.char.direction][0], client.char.y + delta[client.char.direction][1])
                        elif event.key == ord('q'):
                            if os.path.exists('client.json'):
                                os.unlink('client.json')
                            stop_flag.set()

                if inp and client.char:
                    delta = {
                        'A': (-1, 0),
                        'W': (0, -1),
                        'S': (0, 1),
                        'D': (1, 0)
                    }[inp]
                    new_char_x = client.char.x + delta[0]
                    new_char_y = client.char.y + delta[1]
                    target = next((unit for unit in client.game.units if (unit.x, unit.y) == (new_char_x, new_char_y)), None)
                    if target:
                        client.attack(client.char.id, new_char_x, new_char_y)
                    elif client.game.maze.get(new_char_x, new_char_y) == '+':
                        client.open_door(client.char.id, new_char_x, new_char_y)
                    else:
                        client.move_char(client.char.id, new_char_x, new_char_y)

            time.sleep(1 / 25)
    finally:
        if pygame.get_init():
            pygame.quit()


def main():
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(async_main()) #, debug=True)


if __name__ == '__main__':
    main()

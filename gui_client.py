#! /usr/bin/python3

import asyncio
import aiohttp
import copy
import logging
import pygame
from pygame.locals import *
from threading import Thread, Lock
import time

from client import Client
from connection import Connection
from messaging import Codec
import model
import protocol


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
    while True:
        with lock:
            while connection.outgoing:
                message = connection.outgoing.pop(0)
                await ws.send_str(codec.encode(message))
        await asyncio.sleep(0)


async def async_main():
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
        elif s == 'J':
            print('Enter game_id: ', end='')
            game_id = int(input())
            async with session.get('http://localhost:8080/join', params={'name': 'player2', 'game_id': game_id}) as response:
                j = await response.json()
                player_id = j['player_id']
        elif s == 'O':
            print('Enter game_id: ', end='')
            game_id = int(input())
            print('Enter player_id: ', end='')
            player_id = int(input())

        # create client
        connection = Connection()
        client = Client(game_id, player_id, connection)
        client_lock = Lock()

        render_thread = Thread(target=render, args=(client, client_lock))
        render_thread.start()

        # connect
        codec = Codec()
        for obj in (protocol.GetGameRequest, protocol.GetGameResponse, protocol.MoveCharRequest, model.Game, model.Player, model.Maze, model.Unit):
            codec.register(obj)

        logging.debug('Connecting...')
        async with session.ws_connect(f'http://localhost:8080/connect?game_id={game_id}&player_id={player_id}') as ws:
            logging.debug('Connected')
            logging.debug('DIR = %s', dir(ws))

            client.fetch_game()

            read_task = asyncio.create_task(read_socket(ws, codec, connection, client_lock, client))
            write_task = asyncio.create_task(write_socket(ws, codec, connection, client_lock))
            await asyncio.gather(read_task, write_task)

        render_thread.join()


def render(client, lock):
    CELL_SIZE = 32

    pygame.init()
    screen = pygame.display.set_mode((1024, 768))

    while True:
        with lock:
            if not client.game:
                continue

            # Fill background
            background = pygame.Surface(screen.get_size())
            background = background.convert()
            background.fill((0, 0, 0))

            def draw_cell(x, y, color):
                pygame.draw.rect(background, color, (CELL_SIZE * x, CELL_SIZE * y, CELL_SIZE, CELL_SIZE))

            for y, row in enumerate(client.game.maze.map):
                for x, cell in enumerate(row):
                    color = {'.': (200, 200, 200), '|': (240, 240, 240), '-': (240, 240, 240)}[cell]
                    draw_cell(x, y, color)

            draw_cell(client.char.x, client.char.y, (240, 0, 0))

            # Blit everything to the screen
            screen.blit(background, (0, 0))
            pygame.display.flip()

            inp = None
            for event in pygame.event.get():
                if event.type == QUIT:
                    return
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
                        return

            if inp:
                delta = {
                    'A': (-1, 0),
                    'W': (0, -1),
                    'S': (0, 1),
                    'D': (1, 0)
                }[inp]
                client.move_char(client.char.id, client.char.x + delta[0], client.char.y + delta[1])

        time.sleep(1 / 25)


def main():
    logging.basicConfig(level=logging.DEBUG)
    #asyncio.get_event_loop().run_until_complete(async_main())
    asyncio.run(async_main(), debug=True)


if __name__ == '__main__':
    main()

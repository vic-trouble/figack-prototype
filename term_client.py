#! /usr/bin/python3

import asyncio
import aiohttp
import copy
import logging
#import requests
#import websockets

from client import Client
from connection import Connection
from messaging import Codec
import model
import protocol
from threading import Thread, Lock
import time


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
            async with session.get('http://localhost:8080/join', params={'name': 'player2'}) as response:
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
            while connection.outgoing:
                message = connection.outgoing.pop(0)
                await ws.send_str(codec.encode(message))

            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    message = codec.decode(msg.data)
                    connection.incoming.append(message)
                    with client_lock:
                        client.process_connection()
                    while connection.outgoing:
                        message = connection.outgoing.pop(0)
                        await ws.send_str(codec.encode(message))
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    logging.debug('Websocket closed')
                    break
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logging.debug('Websocket error')
                    break

        # render_thread.join()


def render(client, lock):
    fetch_count = -1
    while True:
        with lock:
            if not client.game or client.fetch_count == fetch_count:
                continue

            fetch_count = client.fetch_count

            render_map = copy.deepcopy(client.game.maze.map)
            for ent in client.game.entities.values():
                render_map[ent.y][ent.x] = '@'
            print('-' * 80)
            print('\n'.join(''.join(row) for row in render_map))
            # time.sleep(1)

            print('AWSD? ', end='')
            command = ''
            while not command or command not in 'AWSD':
                command = input().upper()

            delta = {
                'A': (-1, 0),
                'W': (0, -1),
                'S': (0, 1),
                'D': (1, 0)
            }[command]
            client.move_char(client.char.id, client.char.x + delta[0], client.char.y + delta[1])


def main():
    logging.basicConfig(level=logging.DEBUG)
    asyncio.get_event_loop().run_until_complete(async_main())


if __name__ == '__main__':
    main()

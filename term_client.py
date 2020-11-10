#! /usr/bin/python3

import asyncio
import aiohttp
import logging
#import requests
#import websockets

from client import Client
from connection import Connection
from messaging import Codec
import protocol


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

        # connect
        codec = Codec()
        for message in (protocol.GetGameRequest, protocol.GetGameResponse, protocol.MoveCharRequest):
            codec.register(message)

        logging.debug('Connecting...')
        async with session.ws_connect(f'http://localhost:8080/connect?game_id={game_id}&player_id={player_id}') as ws:
            logging.debug('Connected')
            logging.debug('DIR = %s', dir(ws))
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    message = codec.decode(msg.data)
                    connection.incoming.append(message)
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
                render(client)


def render(client):
    print('-' * 80)
    print('\n'.join(''.join(row) for row in client.game.maze.map))


def main():
    logging.basicConfig(level=logging.DEBUG)
    asyncio.get_event_loop().run_until_complete(async_main())


if __name__ == '__main__':
    main()

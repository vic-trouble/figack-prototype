#! /usr/bin/python3

import aiohttp
import aiohttp.web
import asyncio
import json
import logging
import os

from messaging import Codec
import model
from protocol import *
from server import Server

server = Server()

codec = Codec(auto_register=True, globals=globals())


async def handle_create(request):
    logging.debug('Create request')
    name = request.rel_url.query['name']
    response = server.serve(CreateGameRequest(player_name=name))
    return aiohttp.web.json_response({'game_id': response.game_id, 'player_id': response.player_id})


async def handle_join(request):
    logging.debug('Join request')
    game_id = int(request.rel_url.query['game_id'])
    name = request.rel_url.query['name']
    response = server.serve(JoinGameRequest(game_id=game_id, player_name=name))
    return aiohttp.web.json_response({'player_id': response.player_id})


def broadcast_game_changes(connection, serer, game_id):
    for conn in server.get_connections(game_id):
        conn.outgoing.append(GetGameResponse(server.get_game(game_id)))
    server.get_game(game_id).next_tick()


async def read(ws, connection, server, game_id):
    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            request = codec.decode(msg.data)
            logging.debug('IN  %s', msg.data)
            connection.incoming.append(request)
            server.process_connections()  # TODO: do it somewhere outside
            broadcast_game_changes(connection, server, game_id)
        elif msg.type == aiohttp.WSMsgType.ERROR:
            logging.exception(ws.exception())


async def write(ws, connection):
    while True:
        while connection.outgoing:
            message = connection.outgoing.pop(0)
            data = codec.encode(message)
            logging.debug('OUT %s', data)
            await ws.send_str(data)
        await asyncio.sleep(0)


async def simulate(connection, server, game_id):
    while True:
        if server.simulate(game_id):
            broadcast_game_changes(connection, server, game_id)
        await asyncio.sleep(0.5)


async def handle_connect(request):
    game_id = int(request.rel_url.query['game_id'])
    player_id = int(request.rel_url.query['player_id'])
    logging.debug(f'Connect request with game_id={game_id} player_id={player_id}')

    connection = server.connect(game_id, player_id)

    ws = aiohttp.web.WebSocketResponse()
    await ws.prepare(request)

    read_task = asyncio.create_task(read(ws, connection, server, game_id))
    write_task = asyncio.create_task(write(ws, connection))
    simulate_task = asyncio.create_task(simulate(connection, server, game_id))
    await asyncio.gather(read_task, write_task, simulate_task)

    logging.debug('websocket connection closed')
    return ws


def main():
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)-15s %(levelname)s %(message)s')

    if os.path.exists('server.json'):
        with open('server.json') as f:
            try:
                server.load(f)
            except Exception as e:
                print(e)
                print('Load state failed. Remove the file? Y/N')
                yn = input()
                if yn.upper() == 'Y':
                    os.unlink('server.json')

    app = aiohttp.web.Application()
    app.router.add_get('/create', handle_create)
    app.router.add_get('/join', handle_join)
    app.router.add_get('/connect', handle_connect)

    try:
        aiohttp.web.run_app(app)
    finally:
        with open('server.json', 'w') as f:
            server.save(f)


if __name__ == '__main__':
    main()

#! /usr/bin/python3

import aiohttp
import aiohttp.web
import json
import logging

from messaging import Codec
import model
import protocol
from server import Server

server = Server()

codec = Codec()
for obj in (protocol.GetGameRequest, protocol.GetGameResponse, protocol.MoveCharRequest, model.Game, model.Player, model.Maze, model.Unit):
    codec.register(obj)


async def handle_create(request):
    logging.debug('Create request')
    name = request.rel_url.query['name']
    response = server.serve(protocol.CreateGameRequest(player_name=name))
    return aiohttp.web.json_response({'game_id': response.game_id, 'player_id': response.player_id})


async def handle_join(request):
    logging.debug('Join request')
    game_id = int(request.rel_url.query['game_id'])
    name = request.rel_url.query['name']
    response = server.serve(protocol.JoinGameRequest(game_id=game_id, player_name=name))
    return aiohttp.web.json_response({'player_id': response.player_id})


async def handle_connect(request):
    game_id = int(request.rel_url.query['game_id'])
    player_id = int(request.rel_url.query['player_id'])
    logging.debug(f'Connect request with game_id={game_id} player_id={player_id}')

    connection = server.connect(game_id, player_id)

    ws = aiohttp.web.WebSocketResponse()
    await ws.prepare(request)

    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            request = codec.decode(msg.data)
            connection.incoming.append(request)
            server.process_connections()  # TODO: do it somewhere outside
            while connection.outgoing:
                message = connection.outgoing.pop(0)
                await ws.send_str(codec.encode(message))
        elif msg.type == aiohttp.WSMsgType.ERROR:
            logging.exception(ws.exception())

    logging.debug('websocket connection closed')
    return ws


def main():
    logging.basicConfig(level=logging.DEBUG)

    app = aiohttp.web.Application()
    app.router.add_get('/create', handle_create)
    app.router.add_get('/join', handle_join)
    app.router.add_get('/connect', handle_connect)
    aiohttp.web.run_app(app)


if __name__ == '__main__':
    main()

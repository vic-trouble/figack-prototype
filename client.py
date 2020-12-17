import logging
from time import time

from connection import *
from ops import *
from protocol import *


class Client:
    def __init__(self, game_id, player_id, connection: Connection):
        self.connection = connection
        self.game = None
        self.game_id = game_id
        self.player_id = player_id
        self.fetch_count = 0
        self.last_ping_ts = None
        self.last_server_msg_ts = None
        self.last_ping_time = None
        self.reconnect_backoff = 1  # not ideal place for it

    def fetch_game(self):
        self.connection.outgoing.append(GetGameRequest(self.game_id, self.player_id))

    def handle(self, message):
        if isinstance(message, GetGameResponse):
            if not self.game:
                self.game = message.game
            else:
                GameOp(self.game).update_from(message.game)
            self.fetch_count += 1
        elif isinstance(message, PingResponse):
            if self.last_ping_ts:
                self.last_ping_time = time() - self.last_ping_ts
                logging.debug('Ping %f ms', self.last_ping_time * 1000)
            self.last_ping_ts = None

    def process_connection(self):
        while self.connection.incoming:
            self.last_server_msg_ts = time()
            message = self.connection.incoming.pop(0)
            self.handle(message)

    def move_char(self, unit_id, x, y):
        self.connection.outgoing.append(MoveCharRequest(self.game_id, self.player_id, unit_id, x, y))

    @property
    def char(self):
        return next(iter(self.game.units_by_player[self.player_id]), None)

    def attack(self, unit_id, x, y):
        self.connection.outgoing.append(AttackRequest(self.game_id, self.player_id, unit_id, x, y))

    def open_door(self, unit_id, x, y):
        self.connection.outgoing.append(OpenRequest(self.game_id, self.player_id, unit_id, x, y))

    def fire(self, unit_id, x, y):
        self.connection.outgoing.append(FireRequest(self.game_id, self.player_id, unit_id, x, y))

    def ping(self):
        self.connection.outgoing.append(PingRequest())
        self.last_ping_ts = time()

    def on_connected(self):
        self.last_ping_ts = None
        self.last_server_msg_ts = None
        self.reconnect_backoff = 1
        self.fetch_game()

    def jump(self, unit_id, x, y):
        self.connection.outgoing.append(JumpRequest(self.game_id, self.player_id, unit_id, x, y))

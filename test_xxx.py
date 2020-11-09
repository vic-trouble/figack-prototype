import pytest

from connection import *
from client import *
from protocol import *
from server import *


class FakeTransport:
    def __init__(self, server, server_connection, client, client_connection):
        self.client = client
        self.server = server
        self.server_connection = server_connection
        self.client_connection = client_connection

    def sync(self):
        self.server_connection.incoming += self.client_connection.outgoing
        self.client_connection.outgoing.clear()

        self.server.process_connections()

        self.client_connection.incoming += self.server_connection.outgoing
        self.server_connection.outgoing.clear()

        self.client.process_connection()


@pytest.fixture
def server():
    return Server()


@pytest.fixture
def client(server):
    response = server.serve(CreateGameRequest(player_name='player'))

    game_id, player_id = response.game_id, response.player_id
    server_connection = server.connect(game_id, player_id)

    client_connection = Connection()
    client = Client(game_id, player_id, client_connection)
    return client


@pytest.fixture
def transport(server, client):
    return FakeTransport(server, server.get_connection(client.game_id, client.player_id), client, client.connection)


def test_fetch_game(client, server, transport):
    # act
    client.fetch_game()
    transport.sync()

    # assert
    assert client.game.players[client.player_id].name == 'player'

    my_entities = client.game.units_by_player[client.player_id]
    assert len(my_entities) == 1

    char = my_entities[0]
    assert char.player_id == client.player_id
    assert char.id

def test_move_char(client, server, transport):
    # arrange
    client.fetch_game()
    transport.sync()

    char = client.game.units_by_player[client.player_id][0]

    # act
    new_x = char.x - 1 if char.x > 1 else char.x + 1
    client.move_char(char.id, new_x, char.y)

    transport.sync()

    # assert
    assert char.x == new_x

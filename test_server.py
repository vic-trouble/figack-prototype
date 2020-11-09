import protocol
from server import Server


def test_create_game_adds_player():
    # arrange
    server = Server()

    # act
    response = server.serve(protocol.CreateGameRequest(player_name='player'))

    # assert
    assert response.game_id
    assert response.player_id

    assert client.game.players[client.player_id].name == 'player'

"""
def test_join_game_adds_player():
    # arrange
    server = Server()
    client1 = Client(server)
    client1.create_game('player1')

    # act
    client2 = Client(server)
    client2.join_game(client1.game_id, 'player2')

    # assert
    assert client2.player_id
    assert client2.game.players[client2.player_id].name == 'player2'

    assert len(client1.game.players) == 2


def test_create_game_puts_character_in_maze():
    # arrange
    server = Server()
    client = Client(server)

    # act
    client.create_game('player')

    # assert
    my_entities = client.game.units_by_player[client.player_id]
    assert len(my_entities) == 1

    char = my_entities[0]
    assert char.player_id == client.player_id
    assert char.id


def test_move_char():
    # arrange
    server = Server()
    client = Client(server)
    client.create_game('player')

    char = client.game.units_by_player[client.player_id][0]

    # act
    new_x = char.x - 1 if char.x > 1 else char.x + 1
    client.move_char(char.id, new_x, char.y)

    # assert
    assert char.x == new_x
"""
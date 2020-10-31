from client import Client
from server import Server


def test_create_game_adds_player():
    # arrange
    server = Server()
    client = Client(server)

    # act
    client.create_game('player')

    # assert
    assert client.game_token
    assert client.player_id

    client.fetch_game()
    assert client.game.players[client.player_id].name == 'player'


def test_join_game_adds_player():
    # arrange
    server = Server()
    client1 = Client(server)
    client1.create_game('player1')

    # act
    client2 = Client(server)
    client2.join_game(client1.game_token, 'player2')

    # assert
    assert client2.player_id

    client2.fetch_game()
    assert client2.game.players[client2.player_id].name == 'player2'


def test_create_game_puts_character_in_maze():
    # arrange
    server = Server()
    client = Client(server)

    # act
    client.create_game('player')

    # assert
    client.fetch_game()
    
    my_entities = client.game.units_by_player[client.player_id]
    assert len(my_entities) == 1
    
    char = my_entities[0]
    assert char.player_id == client.player_id
    assert char.id

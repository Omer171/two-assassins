import pytest
from helpers import npc_at, put, quiet_game

from two_assassins.game import AP_COSTS, ActionError, Game


def test_r3_turn_starts_with_three_ap():
    assert Game(seed=1).view().ap == 3


def test_r3_action_costs_match_design():
    assert AP_COSTS == {"move": 1, "ask": 1, "hide": 2, "bribe": 2, "disguise": 2,
                        "false_trail": 1, "accuse": 1}


def test_r3_move_costs_one_and_changes_location():
    game = quiet_game()
    put(game, 0, "market")
    game.move("well")
    assert game.players[0].location == "well"
    assert game.ap == 2


def test_r3_move_must_follow_a_connection():
    game = quiet_game()
    put(game, 0, "market")
    with pytest.raises(ActionError):
        game.move("castle")
    assert game.ap == 3
    assert game.players[0].location == "market"


def test_r3_cannot_spend_more_ap_than_left():
    game = quiet_game()
    game.hide()
    with pytest.raises(ActionError):
        game.hide()
    assert game.ap == 1


def test_r3_ap_resets_on_next_turn():
    game = quiet_game()
    game.hide()
    game.end_turn()
    assert game.ap == 3


def test_r3_ask_costs_one():
    game = quiet_game()
    put(game, 0, "market")
    npc = npc_at(game, "market")
    game.ask(npc.cover_id)
    assert game.ap == 2


def test_r3_hidden_player_is_not_noticed_through_other_players_turn():
    game = quiet_game()
    put(game, 0, "market")
    put(game, 1, "castle")
    npc = npc_at(game, "market")
    game.hide()
    game.end_turn()
    npc.location = "market"
    game.end_turn()
    assert all(s.player != 0 for s in npc.memory)


def test_r3_hiding_wears_off_when_your_next_turn_starts():
    game = quiet_game()
    game.hide()
    game.end_turn()
    assert game.players[0].hidden
    game.end_turn()
    assert not game.players[0].hidden


def test_r3_moving_cancels_hiding():
    game = quiet_game()
    put(game, 0, "market")
    game.hide()
    game.move("well")
    assert not game.players[0].hidden

import pytest
from helpers import npc_at, put, quiet_game

from two_assassins.game import ActionError


def meeting(seed=1):
    game = quiet_game(seed=seed)
    put(game, 0, "market")
    put(game, 1, "market")
    return game, npc_at(game, "market")


def test_r6_correct_accusation_wins():
    game, _ = meeting()
    game.accuse(game.players[1].cover_id)
    assert game.over
    assert game.winner == 0
    assert game.end_reason == "accusation"


def test_r6_wrong_accusation_tells_other_player_where_accuser_is():
    game, npc = meeting()
    game.accuse(npc.cover_id)
    assert not game.over
    reveal = game.players[1].clues[-1]
    assert reveal.source == "accusation"
    assert reveal.location == "market"
    assert reveal.is_true


def test_r6_accusation_costs_one_ap_and_only_once_per_turn():
    game, npc = meeting()
    game.accuse(npc.cover_id)
    assert game.ap == 2
    with pytest.raises(ActionError):
        game.accuse(game.players[1].cover_id)
    assert not game.view().can_accuse
    game.end_turn()
    assert game.view().can_accuse


def test_r6_can_only_accuse_someone_at_your_location():
    game = quiet_game()
    put(game, 0, "market")
    put(game, 1, "castle")
    with pytest.raises(ActionError):
        game.accuse(game.players[1].cover_id)
    with pytest.raises(ActionError):
        game.accuse(game.players[0].cover_id)


def test_r6_no_actions_after_game_is_won():
    game, npc = meeting()
    game.accuse(game.players[1].cover_id)
    with pytest.raises(ActionError):
        game.ask(npc.cover_id)
    with pytest.raises(ActionError):
        game.end_turn()

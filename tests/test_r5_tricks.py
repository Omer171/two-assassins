import pytest
from helpers import npc_at, put, quiet_game, sighting

from two_assassins.game import ActionError


def bribe_then_ask(seed=1):
    """On turn 3 player 0 bribes an NPC at the market; on turn 4 player 1 asks it."""
    game = quiet_game(seed=seed)
    put(game, 0, "market")
    put(game, 1, "castle")
    game.end_turn()
    game.end_turn()           # turn 3, player 0 again
    npc = npc_at(game, "market")
    game.bribe(npc.cover_id)
    color = game.players[0].disguise.color
    game.end_turn()           # turn 4, player 1
    npc.location = "market"
    put(game, 1, "market")
    return game, npc, color


def test_r5_bribe_costs_two_and_marks_npc():
    game = quiet_game()
    put(game, 0, "market")
    npc = npc_at(game, "market")
    game.bribe(npc.cover_id)
    assert game.ap == 1
    assert npc.bribed_by == 0
    assert npc.bribe_color == game.players[0].disguise.color


def test_r5_bribed_npc_lies_to_the_next_asker():
    for seed in range(20):
        game, npc, color = bribe_then_ask(seed)
        game.ask(npc.cover_id)
        lie = game.players[1].clues[-1]
        assert not lie.is_true
        assert lie.color == color
        real = game.location_at(0, lie.actual_turn)
        assert lie.location != real


def test_r5_bribe_only_fools_one_ask():
    game, npc, _ = bribe_then_ask()
    game.ask(npc.cover_id)
    assert npc.bribed_by is None
    npc.memory.append(sighting(turn=game.turn - 1, location="market", player=0))
    game.ask(npc.cover_id)
    assert game.players[1].clues[-1].is_true


def test_r5_bribing_the_other_player_looks_like_bribing_an_npc():
    game = quiet_game()
    put(game, 0, "market")
    put(game, 1, "market")
    npc = npc_at(game, "market")
    msg_player = game.bribe(game.players[1].cover_id)
    game.ap = 3
    msg_npc = game.bribe(npc.cover_id)
    assert msg_player.replace(str(game.players[1].cover_id), "#") == \
        msg_npc.replace(str(npc.cover_id), "#")


def test_r5_disguise_changes_color_and_costs_two():
    for seed in range(20):
        game = quiet_game(seed=seed)
        old = game.players[0].disguise
        game.disguise()
        assert game.players[0].disguise.color != old.color
        assert game.ap == 1


def test_r5_old_clues_keep_the_old_color_after_disguise():
    game = quiet_game()
    put(game, 0, "market")
    npc = npc_at(game, "market")
    old_color = game.players[0].disguise.color
    game.end_turn()           # NPC sees player 0 in the old disguise
    game.end_turn()
    game.disguise()
    assert all(s.color == old_color for s in npc.memory if s.player == 0)
    assert game.players[0].disguise.color != old_color


def test_r5_false_trail_only_where_you_have_never_been():
    game = quiet_game()
    put(game, 0, "market")
    with pytest.raises(ActionError):
        game.false_trail("market")
    target = next(loc for loc in game.view().trail_targets)
    game.false_trail(target)
    assert game.ap == 2
    assert game.trails[-1].location == target


def test_r5_trail_targets_exclude_visited_places():
    game = quiet_game()
    put(game, 0, "market")
    game.move("well")
    targets = game.view().trail_targets
    assert "market" not in targets and "well" not in targets


def test_r5_other_player_finds_false_trail_when_entering():
    game = quiet_game()
    put(game, 0, "castle")
    game.players[0].visited = {"castle"}
    game.false_trail("tavern")
    game.end_turn()
    put(game, 1, "market")
    game.move("tavern")
    found = game.players[1].clues[-1]
    assert found.source == "trail"
    assert found.location == "tavern"
    assert not found.is_true
    assert game.trails == []


def test_r5_other_player_finds_trail_when_turn_starts_there():
    game = quiet_game()
    put(game, 0, "castle")
    game.players[0].visited = {"castle"}
    put(game, 1, "docks")
    game.false_trail("docks")
    game.end_turn()
    assert game.players[1].clues[-1].source == "trail"


def test_r5_you_do_not_find_your_own_trail():
    game = quiet_game()
    put(game, 0, "market")
    game.players[0].visited = {"market"}
    game.false_trail("well")
    game.move("well")
    assert game.players[0].clues == []
    assert len(game.trails) == 1

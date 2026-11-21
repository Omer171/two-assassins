import dataclasses

from helpers import clue, npc_at, put, quiet_game

from two_assassins.game import Game


def test_r2_players_alternate_turns():
    game = Game(seed=1)
    order = []
    for _ in range(4):
        order.append((game.turn, game.current))
        game.end_turn()
    assert order == [(1, 0), (2, 1), (3, 0), (4, 1)]


def test_r2_view_belongs_to_current_player():
    game = Game(seed=1)
    view = game.view()
    assert view.player == 0
    assert view.location == game.players[0].location
    assert view.disguise == game.players[0].disguise.describe()
    game.end_turn()
    assert game.view().player == 1
    assert game.view().location == game.players[1].location


def test_r2_view_has_no_field_for_the_other_player():
    names = {f.name for f in dataclasses.fields(Game(seed=1).view())}
    assert names == {"player", "turn", "max_turns", "ap", "location", "neighbors", "disguise",
                     "hidden", "people_here", "clues", "can_accuse", "trail_targets"}


def test_r2_view_is_unchanged_when_other_player_moves_elsewhere():
    game = quiet_game(seed=2)
    put(game, 0, "market")
    put(game, 1, "castle")
    before = game.view()
    put(game, 1, "docks")
    assert game.view() == before


def test_r2_other_player_here_looks_like_any_npc():
    game = quiet_game(seed=2)
    put(game, 0, "market")
    put(game, 1, "market")
    npc = npc_at(game, "market")
    people = game.view().people_here
    ids = {p.cover_id for p in people}
    assert ids == {npc.cover_id, game.players[1].cover_id}
    assert game.players[0].cover_id not in ids
    assert {f.name for f in dataclasses.fields(people[0])} == {"cover_id", "appearance"}


def test_r2_clue_view_does_not_reveal_truth():
    game = quiet_game(seed=2)
    game.players[0].clues.append(clue(0, False))
    shown = game.view().clues[0]
    assert not hasattr(shown, "is_true")
    assert not hasattr(shown, "source")


def test_r2_clues_are_private_to_their_player():
    game = quiet_game(seed=2)
    game.players[0].clues.append(clue(0, True))
    assert len(game.view().clues) == 1
    game.end_turn()
    assert game.view().clues == ()

from helpers import clue, quiet_game

from two_assassins.game import Game


def play_to_dawn(game):
    while not game.over:
        game.end_turn()


def test_r7_default_dawn_is_after_30_turns():
    game = Game(seed=1)
    assert game.max_turns == 30
    for _ in range(29):
        game.end_turn()
    assert not game.over
    game.end_turn()
    assert game.over
    assert game.end_reason == "dawn"


def test_r7_more_true_clues_wins_at_dawn():
    game = quiet_game(max_turns=2)
    game.players[0].clues += [clue(0, True), clue(0, True), clue(0, False)]
    game.players[1].clues += [clue(1, True), clue(1, False), clue(1, False), clue(1, False)]
    play_to_dawn(game)
    assert game.scores() == (2, 1)
    assert game.winner == 0


def test_r7_tie_is_a_draw():
    game = quiet_game(max_turns=2)
    game.players[0].clues += [clue(0, True)]
    game.players[1].clues += [clue(1, True), clue(1, False)]
    play_to_dawn(game)
    assert game.winner is None
    assert game.end_reason == "dawn"


def test_r7_lies_and_false_trails_do_not_score():
    game = quiet_game(max_turns=2)
    game.players[1].clues += [clue(1, False), clue(1, False)]
    play_to_dawn(game)
    assert game.scores() == (0, 0)
    assert game.winner is None

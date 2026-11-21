from helpers import npc_at, put, quiet_game, sighting

from two_assassins.clues import CLUE_MAX_AGE, CLUE_MIN_AGE
from two_assassins.game import COLORS, GARMENTS


def asking_setup(seed=1, turn=6):
    """Player 0 at the market with one NPC; player 1 far away at the castle."""
    game = quiet_game(seed=seed)
    game.turn = turn
    put(game, 0, "market")
    put(game, 1, "castle")
    return game, npc_at(game, "market")


def test_r4_clue_tells_where_other_player_was_not_where_they_are():
    game, npc = asking_setup()
    npc.memory.append(sighting(turn=4, location="well", player=1))
    game.ask(npc.cover_id)
    got = game.players[0].clues[-1]
    assert got.location == "well"
    assert got.location != game.players[1].location
    assert got.is_true


def test_r4_sightings_from_this_turn_are_not_reported():
    game, npc = asking_setup()
    npc.memory.append(sighting(turn=6, location="market", player=1))
    game.ask(npc.cover_id)
    assert game.players[0].clues == []


def test_r4_sightings_older_than_three_turns_are_forgotten():
    game, npc = asking_setup()
    npc.memory.append(sighting(turn=6 - CLUE_MAX_AGE - 1, location="well", player=1))
    game.ask(npc.cover_id)
    assert game.players[0].clues == []


def test_r4_npc_does_not_report_on_the_asker():
    game, npc = asking_setup()
    npc.memory.append(sighting(turn=5, location="market", player=0))
    game.ask(npc.cover_id)
    assert game.players[0].clues == []


def test_r4_reported_age_is_off_by_at_most_one():
    seen_ages = set()
    for seed in range(40):
        for true_age in range(CLUE_MIN_AGE, CLUE_MAX_AGE + 1):
            game, npc = asking_setup(seed=seed)
            npc.memory.append(sighting(turn=6 - true_age, location="well", player=1))
            game.ask(npc.cover_id)
            reported = game.players[0].clues[-1].reported_age
            assert reported >= 1
            assert abs(reported - true_age) <= 1
            seen_ages.add(reported - true_age)
    assert seen_ages == {-1, 0, 1}


def test_r4_clue_names_color_but_not_garment():
    game, npc = asking_setup()
    npc.memory.append(sighting(turn=5, location="well", player=1, color="green"))
    game.ask(npc.cover_id)
    text = game.players[0].clues[-1].text
    assert "green" in text and "well" in text
    assert not any(g in text for g in GARMENTS)
    assert not any(c in text for c in COLORS if c != "green")


def test_r4_npcs_notice_players_at_end_of_turn():
    game = quiet_game()
    put(game, 1, "tavern")
    npc = npc_at(game, "tavern")
    game.end_turn()
    assert any(s.player == 1 and s.location == "tavern" and s.turn == 1 for s in npc.memory)


def test_r4_npcs_notice_player_passing_through():
    game = quiet_game()
    put(game, 0, "market")
    npc = npc_at(game, "well")
    game.move("well")
    game.move("church")
    assert any(s.player == 0 and s.location == "well" for s in npc.memory)


def test_r4_clue_reaches_asker_only_after_delay_in_real_play():
    game = quiet_game()
    put(game, 0, "market")
    put(game, 1, "tavern")
    npc = npc_at(game, "tavern")
    game.end_turn()           # turn 1 ends: NPC sees player 1 at the tavern
    game.end_turn()           # turn 2 (player 1) ends
    put(game, 0, "tavern")    # turn 3: player 0 reaches the tavern
    npc.location = "tavern"
    game.ask(npc.cover_id)
    assert any(c.location == "tavern" and c.is_true for c in game.players[0].clues)

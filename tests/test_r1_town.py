from two_assassins import town
from two_assassins.game import COLORS, GARMENTS, Game


def test_r1_town_has_medieval_locations():
    for name in ("market", "well", "church", "tavern", "blacksmith", "gates"):
        assert name in town.LOCATIONS


def test_r1_connections_go_both_ways():
    for place, links in town.TOWN_MAP.items():
        for other in links:
            assert place in town.TOWN_MAP[other]


def test_r1_every_location_is_reachable():
    for place in town.LOCATIONS:
        assert town.distance("market", place) is not None


def test_r1_distance_counts_steps():
    assert town.distance("market", "market") == 0
    assert town.distance("market", "well") == 1
    assert town.distance("graveyard", "docks") == 3


def test_r1_town_is_filled_with_npcs_at_real_locations():
    game = Game(seed=3)
    assert len(game.npcs) == 14
    assert all(npc.location in town.LOCATIONS for npc in game.npcs)


def test_r1_npcs_only_move_to_connected_locations():
    game = Game(seed=5)
    for _ in range(10):
        before = [npc.location for npc in game.npcs]
        game.end_turn()
        for old, npc in zip(before, game.npcs):
            assert npc.location == old or npc.location in town.TOWN_MAP[old]


def test_r1_npcs_move_on_their_own():
    game = Game(seed=5)
    before = [npc.location for npc in game.npcs]
    for _ in range(5):
        game.end_turn()
    assert before != [npc.location for npc in game.npcs]


def test_r1_players_start_apart_in_different_places():
    for seed in range(60):
        game = Game(seed=seed)
        a, b = game.players
        assert a.location != b.location
        assert town.distance(a.location, b.location) >= town.MIN_START_DISTANCE


def test_r1_players_start_disguised_as_townspeople():
    game = Game(seed=8)
    for player in game.players:
        assert player.disguise.color in COLORS
        assert player.disguise.garment in GARMENTS


def test_r1_cover_numbers_are_unique_across_npcs_and_players():
    game = Game(seed=8)
    ids = [p.cover_id for p in game.players] + [n.cover_id for n in game.npcs]
    assert len(set(ids)) == len(ids)


def test_r1_same_seed_builds_same_town():
    a, b = Game(seed=42), Game(seed=42)
    assert [n.location for n in a.npcs] == [n.location for n in b.npcs]
    assert [p.location for p in a.players] == [p.location for p in b.players]
    assert [p.disguise for p in a.players] == [p.disguise for p in b.players]

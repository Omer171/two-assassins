import json

from helpers import npc_at, put, quiet_game, sighting

from two_assassins import town
from two_assassins.replay import read_jsonl, write_jsonl


def short_game():
    game = quiet_game(seed=4, max_turns=4)
    put(game, 0, "market")
    put(game, 1, "castle")
    game.move("well")
    game.end_turn()
    game.move("docks")
    game.end_turn()
    npc = npc_at(game, "well")
    npc.memory.append(sighting(turn=2, location="docks", player=1))
    game.ask(npc.cover_id)
    game.end_turn()
    game.end_turn()
    return game


def test_r8_replay_has_both_positions_every_turn():
    data = short_game().replay()
    assert [t["turn"] for t in data["turns"]] == [1, 2, 3, 4]
    assert data["turns"][0]["positions"] == ["well", "castle"]
    assert data["turns"][1]["positions"] == ["well", "docks"]
    assert data["turns"][0]["actions"] == ["move well"]
    assert data["turns"][1]["distance"] == town.distance("well", "docks")


def test_r8_replay_includes_map_and_start():
    data = short_game().replay()
    assert set(data["map"]) == set(town.LOCATIONS)
    assert len(data["start"]) == 2


def test_r8_replay_marks_true_and_false_clues():
    game = short_game()
    data = game.replay()
    assert [c["is_true"] for c in data["clues"]] == [True]
    assert data["clues"][0]["receiver"] == 0


def test_r8_replay_has_result():
    data = short_game().replay()
    assert data["result"] == {"winner": 0, "reason": "dawn", "scores": [1, 0]}


def test_r8_replay_is_json_and_survives_jsonl_round_trip(tmp_path):
    data = short_game().replay()
    path = tmp_path / "replay.jsonl"
    write_jsonl(data, path)
    lines = path.read_text(encoding="utf-8").splitlines()
    assert json.loads(lines[0])["type"] == "meta"
    assert json.loads(lines[-1])["type"] == "result"
    assert read_jsonl(path) == data


def test_r8_winning_turn_is_recorded():
    game = quiet_game()
    put(game, 0, "market")
    put(game, 1, "market")
    game.accuse(game.players[1].cover_id)
    last = game.replay()["turns"][-1]
    assert last["turn"] == 1
    assert last["actions"] == ["accuse #%d (correct)" % game.players[1].cover_id]

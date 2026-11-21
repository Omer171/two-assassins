"""Shared setup helpers for the tests. They put the game into exact states."""
from two_assassins.clues import Clue, Sighting
from two_assassins.game import Game

PARKING = "graveyard"  # where unused NPCs are sent so they stay out of the way


def quiet_game(seed=1, **kwargs):
    """A game where every NPC is parked at the graveyard with no memory or bribe."""
    game = Game(seed=seed, **kwargs)
    for npc in game.npcs:
        npc.location = PARKING
        npc.memory.clear()
        npc.bribed_by = None
    return game


def npc_at(game, location, index=0):
    npc = game.npcs[index]
    npc.location = location
    npc.memory.clear()
    npc.bribed_by = None
    return npc


def put(game, pid, location):
    game.players[pid].location = location
    game.players[pid].visited.add(location)


def sighting(turn, location, player, color="red"):
    return Sighting(turn=turn, location=location, player=player, color=color)


def clue(receiver, is_true, location="well"):
    return Clue(receiver=receiver, turn_received=1, source="npc" if is_true else "bribe",
                location=location, text="test clue", is_true=is_true)

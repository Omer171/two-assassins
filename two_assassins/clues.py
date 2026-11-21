"""R4: what NPCs remember, and turning memories (or bribes) into clues."""
from dataclasses import dataclass
from typing import Callable, List, Optional

from .town import LOCATIONS

CLUE_MIN_AGE = 1   # a sighting from this turn is never reported: clues are always delayed
CLUE_MAX_AGE = 3   # older sightings are forgotten
AGE_FUZZ = 1       # the reported age may be off by this many turns


@dataclass(frozen=True)
class Sighting:
    turn: int
    location: str
    player: int
    color: str


@dataclass
class Clue:
    receiver: int
    turn_received: int
    source: str          # "npc", "bribe", "trail" or "accusation"
    location: str
    text: str
    is_true: bool
    color: Optional[str] = None
    reported_age: Optional[int] = None
    actual_turn: Optional[int] = None   # turn the clue claims to describe


def recent_sightings(memory: List[Sighting], player: int, now: int) -> List[Sighting]:
    return [s for s in memory
            if s.player == player and CLUE_MIN_AGE <= now - s.turn <= CLUE_MAX_AGE]


def fuzz_age(rng, true_age: int) -> int:
    return max(1, true_age + rng.randint(-AGE_FUZZ, AGE_FUZZ))


def npc_clue_text(speaker: int, color: str, location: str, age: int) -> str:
    ago = "1 turn ago" if age == 1 else "%d turns ago" % age
    return '#%d says: "Someone in %s passed the %s about %s."' % (speaker, color, location, ago)


def make_true_clue(rng, seen: Sighting, now: int, receiver: int, speaker: int) -> Clue:
    age = fuzz_age(rng, now - seen.turn)
    return Clue(receiver=receiver, turn_received=now, source="npc", location=seen.location,
                text=npc_clue_text(speaker, seen.color, seen.location, age), is_true=True,
                color=seen.color, reported_age=age, actual_turn=seen.turn)


def make_lie(rng, now: int, receiver: int, speaker: int, color: str,
             location_at: Callable[[int], str]) -> Clue:
    """A clue that looks real but names a place the briber was not at the claimed time."""
    true_age = rng.randint(CLUE_MIN_AGE, CLUE_MAX_AGE)
    claimed_turn = now - true_age
    real = location_at(claimed_turn)
    location = rng.choice([loc for loc in LOCATIONS if loc != real])
    age = fuzz_age(rng, true_age)
    return Clue(receiver=receiver, turn_received=now, source="bribe", location=location,
                text=npc_clue_text(speaker, color, location, age), is_true=False,
                color=color, reported_age=age, actual_turn=claimed_turn)

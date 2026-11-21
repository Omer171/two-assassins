"""Rules of Two Assassins (R1-R8). Nothing here prints or reads input.

Action methods act for the current player and return a message string for the
front end. They raise ActionError when the rules forbid the action; a refused
action costs nothing.
"""
import random
from dataclasses import dataclass, field
from typing import List, Optional, Set, Tuple, Union

from .clues import Clue, Sighting, make_lie, make_true_clue, recent_sightings
from .town import LOCATIONS, TOWN_MAP, choose_start_locations, distance, npc_step

COLORS = ("red", "blue", "green", "brown", "grey", "black", "yellow", "white")
GARMENTS = ("hood", "cloak", "apron", "tunic", "hat")
TRAIL_ITEMS = ("dagger", "glove", "coin purse", "torn scarf")

AP_COSTS = {"move": 1, "ask": 1, "hide": 2, "bribe": 2, "disguise": 2,
            "false_trail": 1, "accuse": 1}
DEFAULT_AP_PER_TURN = 3
DEFAULT_MAX_TURNS = 30
DEFAULT_NPC_COUNT = 14


class ActionError(ValueError):
    """The current player tried something the rules do not allow."""


@dataclass(frozen=True)
class Appearance:
    color: str
    garment: str

    def describe(self) -> str:
        return "%s %s" % (self.color, self.garment)


def random_appearance(rng, avoid_color: Optional[str] = None) -> Appearance:
    colors = [c for c in COLORS if c != avoid_color]
    return Appearance(rng.choice(colors), rng.choice(GARMENTS))


@dataclass
class NPC:
    cover_id: int
    location: str
    appearance: Appearance
    memory: List[Sighting] = field(default_factory=list)
    bribed_by: Optional[int] = None
    bribe_color: Optional[str] = None


@dataclass
class Player:
    pid: int
    cover_id: int
    location: str
    disguise: Appearance
    hidden: bool = False
    visited: Set[str] = field(default_factory=set)
    clues: List[Clue] = field(default_factory=list)

    def __post_init__(self):
        self.visited.add(self.location)


@dataclass
class Trail:
    owner: int
    location: str
    color: str
    item: str
    turn_placed: int


@dataclass(frozen=True)
class TurnRecord:
    turn: int
    player: int
    actions: Tuple[str, ...]
    positions: Tuple[str, str]
    hidden: Tuple[bool, bool]
    colors: Tuple[str, str]


@dataclass(frozen=True)
class PersonView:
    cover_id: int
    appearance: str


@dataclass(frozen=True)
class ClueView:
    turn_received: int
    text: str
    location: str
    color: Optional[str]
    reported_age: Optional[int]


@dataclass(frozen=True)
class PlayerView:
    """Everything the current player may see (R2). Never the rival's location."""
    player: int
    turn: int
    max_turns: int
    ap: int
    location: str
    neighbors: Tuple[str, ...]
    disguise: str
    hidden: bool
    people_here: Tuple[PersonView, ...]
    clues: Tuple[ClueView, ...]
    can_accuse: bool
    trail_targets: Tuple[str, ...]


class Game:
    def __init__(self, seed: Optional[int] = None, max_turns: int = DEFAULT_MAX_TURNS,
                 ap_per_turn: int = DEFAULT_AP_PER_TURN, npc_count: int = DEFAULT_NPC_COUNT):
        self.seed = seed
        self.rng = random.Random(seed)
        self.max_turns = max_turns
        self.ap_per_turn = ap_per_turn

        cover_ids = list(range(1, npc_count + 3))
        self.rng.shuffle(cover_ids)
        start_a, start_b = choose_start_locations(self.rng)
        self.start_locations = (start_a, start_b)
        self.players = [
            Player(0, cover_ids[0], start_a, random_appearance(self.rng)),
            Player(1, cover_ids[1], start_b, random_appearance(self.rng)),
        ]
        self.npcs = [NPC(cid, self.rng.choice(LOCATIONS), random_appearance(self.rng))
                     for cid in cover_ids[2:]]

        self.turn = 1
        self.current = 0
        self.ap = ap_per_turn
        self.accused_this_turn = False
        self.trails: List[Trail] = []
        self.winner: Optional[int] = None
        self.end_reason: Optional[str] = None
        self.turn_log: List[TurnRecord] = []
        self.clue_log: List[Clue] = []
        self._actions: List[str] = []

    # ----- state helpers -------------------------------------------------

    @property
    def over(self) -> bool:
        return self.end_reason is not None

    @property
    def current_player(self) -> Player:
        return self.players[self.current]

    @property
    def opponent(self) -> Player:
        return self.players[1 - self.current]

    def location_at(self, pid: int, turn: int) -> str:
        """Where a player was at the end of a past turn (start location before turn 1)."""
        where = self.start_locations[pid]
        for record in self.turn_log:
            if record.turn > turn:
                break
            where = record.positions[pid]
        return where

    def scores(self) -> Tuple[int, int]:
        return tuple(sum(1 for c in p.clues if c.is_true) for p in self.players)

    def _begin(self, action: str) -> int:
        if self.over:
            raise ActionError("The game is over.")
        cost = AP_COSTS[action]
        if self.ap < cost:
            raise ActionError("That costs %d AP but you have %d left." % (cost, self.ap))
        return cost

    def _person_here(self, cover_id: int) -> Union[NPC, Player]:
        me, rival = self.current_player, self.opponent
        for npc in self.npcs:
            if npc.cover_id == cover_id and npc.location == me.location:
                return npc
        if rival.cover_id == cover_id and rival.location == me.location:
            return rival
        raise ActionError("There is nobody called #%d at the %s." % (cover_id, me.location))

    def _see(self, npc: NPC, player: Player) -> None:
        if player.hidden or npc.location != player.location:
            return
        seen = Sighting(self.turn, player.location, player.pid, player.disguise.color)
        if seen not in npc.memory:
            npc.memory.append(seen)

    def _give_clue(self, clue: Clue) -> None:
        self.players[clue.receiver].clues.append(clue)
        self.clue_log.append(clue)

    def _discover_trails(self, player: Player) -> List[str]:
        found = [t for t in self.trails if t.owner != player.pid and t.location == player.location]
        messages = []
        for trail in found:
            self.trails.remove(trail)
            text = ("You find a dropped %s at the %s. Someone in %s must have been here."
                    % (trail.item, trail.location, trail.color))
            self._give_clue(Clue(receiver=player.pid, turn_received=self.turn, source="trail",
                                 location=trail.location, text=text, is_true=False,
                                 color=trail.color))
            messages.append(text)
        return messages

    def _record_turn(self) -> None:
        a, b = self.players
        self.turn_log.append(TurnRecord(
            turn=self.turn, player=self.current, actions=tuple(self._actions),
            positions=(a.location, b.location), hidden=(a.hidden, b.hidden),
            colors=(a.disguise.color, b.disguise.color)))
        self._actions = []

    # ----- actions (R3, R4, R5, R6) -------------------------------------

    def move(self, destination: str) -> str:
        cost = self._begin("move")
        me = self.current_player
        if destination not in TOWN_MAP[me.location]:
            raise ActionError("The %s is not connected to the %s." % (destination, me.location))
        self.ap -= cost
        me.location = destination
        me.hidden = False
        me.visited.add(destination)
        for npc in self.npcs:
            self._see(npc, me)
        self._actions.append("move " + destination)
        return " ".join(["You walk to the %s." % destination] + self._discover_trails(me))

    def ask(self, cover_id: int) -> str:
        cost = self._begin("ask")
        person = self._person_here(cover_id)
        self.ap -= cost
        self._actions.append("ask #%d" % cover_id)
        me, rival = self.current_player, self.opponent
        clue = None
        if isinstance(person, NPC):
            if person.bribed_by == rival.pid:
                clue = make_lie(self.rng, self.turn, me.pid, person.cover_id, person.bribe_color,
                                lambda t: self.location_at(rival.pid, t))
                person.bribed_by = person.bribe_color = None
            else:
                seen = recent_sightings(person.memory, rival.pid, self.turn)
                if seen:
                    clue = make_true_clue(self.rng, self.rng.choice(seen), self.turn,
                                          me.pid, person.cover_id)
        if clue is None:
            return '#%d says: "I haven\'t seen anyone suspicious lately."' % cover_id
        self._give_clue(clue)
        return clue.text

    def hide(self) -> str:
        cost = self._begin("hide")
        self.ap -= cost
        self.current_player.hidden = True
        self._actions.append("hide")
        return "You keep to the shadows. Townsfolk won't notice you until your next turn."

    def bribe(self, cover_id: int) -> str:
        cost = self._begin("bribe")
        person = self._person_here(cover_id)
        self.ap -= cost
        me = self.current_player
        if isinstance(person, NPC):
            person.bribed_by = me.pid
            person.bribe_color = me.disguise.color
        self._actions.append("bribe #%d" % cover_id)
        return "#%d pockets your coin and winks." % cover_id

    def disguise(self) -> str:
        cost = self._begin("disguise")
        self.ap -= cost
        me = self.current_player
        me.disguise = random_appearance(self.rng, avoid_color=me.disguise.color)
        self._actions.append("disguise " + me.disguise.describe())
        return "You are now wearing a %s." % me.disguise.describe()

    def false_trail(self, location: str) -> str:
        cost = self._begin("false_trail")
        me = self.current_player
        if location not in TOWN_MAP:
            raise ActionError("There is no place called %r." % location)
        if location in me.visited:
            raise ActionError("You have been to the %s; a trail must go where you never went."
                              % location)
        self.ap -= cost
        item = self.rng.choice(TRAIL_ITEMS)
        self.trails.append(Trail(me.pid, location, me.disguise.color, item, self.turn))
        self._actions.append("false_trail " + location)
        return "A street urchin will drop a %s at the %s for you." % (item, location)

    def accuse(self, cover_id: int) -> str:
        cost = self._begin("accuse")
        if self.accused_this_turn:
            raise ActionError("You can only accuse once per turn.")
        person = self._person_here(cover_id)
        self.ap -= cost
        self.accused_this_turn = True
        me, rival = self.current_player, self.opponent
        if person is rival:
            self._actions.append("accuse #%d (correct)" % cover_id)
            self.winner = me.pid
            self.end_reason = "accusation"
            self._record_turn()
            return "#%d is unmasked! You win." % cover_id
        self._actions.append("accuse #%d (wrong)" % cover_id)
        self._give_clue(Clue(
            receiver=rival.pid, turn_received=self.turn, source="accusation",
            location=me.location, is_true=True, color=me.disguise.color, reported_age=0,
            actual_turn=self.turn,
            text="Word spreads: on turn %d someone in %s wrongly accused #%d at the %s. "
                 "That was the other assassin!" % (self.turn, me.disguise.color, cover_id,
                                                   me.location)))
        return "#%d is just a townsperson. The other assassin will hear where you are." % cover_id

    # ----- turn flow (R2, R7) -------------------------------------------

    def end_turn(self) -> str:
        if self.over:
            raise ActionError("The game is over.")
        for npc in self.npcs:
            for player in self.players:
                self._see(npc, player)
        self._record_turn()
        for npc in self.npcs:
            npc.location = npc_step(self.rng, npc.location)
        if self.turn >= self.max_turns:
            self._finish_at_dawn()
            return "Dawn breaks."
        self.turn += 1
        self.current = 1 - self.current
        self.ap = self.ap_per_turn
        self.accused_this_turn = False
        nxt = self.current_player
        nxt.hidden = False
        return " ".join(self._discover_trails(nxt))

    def _finish_at_dawn(self) -> None:
        a, b = self.scores()
        self.winner = 0 if a > b else 1 if b > a else None
        self.end_reason = "dawn"

    # ----- what a player may see (R2) -----------------------------------

    def view(self) -> PlayerView:
        me, rival = self.current_player, self.opponent
        people = [PersonView(n.cover_id, n.appearance.describe())
                  for n in self.npcs if n.location == me.location]
        if rival.location == me.location:
            people.append(PersonView(rival.cover_id, rival.disguise.describe()))
        people.sort(key=lambda p: p.cover_id)
        return PlayerView(
            player=me.pid, turn=self.turn, max_turns=self.max_turns, ap=self.ap,
            location=me.location, neighbors=TOWN_MAP[me.location],
            disguise=me.disguise.describe(), hidden=me.hidden, people_here=tuple(people),
            clues=tuple(ClueView(c.turn_received, c.text, c.location, c.color, c.reported_age)
                        for c in me.clues),
            can_accuse=not self.accused_this_turn,
            trail_targets=tuple(loc for loc in LOCATIONS if loc not in me.visited))

    # ----- replay data (R8) ---------------------------------------------

    def replay(self) -> dict:
        return {
            "seed": self.seed,
            "max_turns": self.max_turns,
            "map": {loc: list(links) for loc, links in TOWN_MAP.items()},
            "start": list(self.start_locations),
            "turns": [{
                "turn": r.turn, "player": r.player, "actions": list(r.actions),
                "positions": list(r.positions), "hidden": list(r.hidden),
                "colors": list(r.colors), "distance": distance(*r.positions),
            } for r in self.turn_log],
            "clues": [{
                "receiver": c.receiver, "turn_received": c.turn_received, "source": c.source,
                "location": c.location, "text": c.text, "is_true": c.is_true,
            } for c in self.clue_log],
            "result": {"winner": self.winner, "reason": self.end_reason,
                       "scores": list(self.scores())},
        }

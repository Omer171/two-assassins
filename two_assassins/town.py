"""R1: the town map, distances, starting positions and NPC movement."""
from collections import deque
from typing import Dict, List, Optional, Tuple

TOWN_MAP: Dict[str, Tuple[str, ...]] = {
    "gates": ("market", "graveyard", "stables"),
    "market": ("gates", "well", "tavern", "blacksmith"),
    "well": ("market", "church", "tavern"),
    "church": ("well", "graveyard", "castle"),
    "graveyard": ("gates", "church"),
    "tavern": ("market", "well", "docks"),
    "blacksmith": ("market", "docks", "stables"),
    "docks": ("tavern", "blacksmith", "castle"),
    "castle": ("church", "docks"),
    "stables": ("gates", "blacksmith"),
}
LOCATIONS: Tuple[str, ...] = tuple(TOWN_MAP)
MIN_START_DISTANCE = 3


def distance(start: str, goal: str) -> Optional[int]:
    """Number of steps on the shortest path, or None if goal is unreachable."""
    seen = {start: 0}
    queue = deque([start])
    while queue:
        here = queue.popleft()
        if here == goal:
            return seen[here]
        for nxt in TOWN_MAP[here]:
            if nxt not in seen:
                seen[nxt] = seen[here] + 1
                queue.append(nxt)
    return None


def far_apart_pairs(min_distance: int = MIN_START_DISTANCE) -> List[Tuple[str, str]]:
    return [(a, b) for a in LOCATIONS for b in LOCATIONS
            if a != b and distance(a, b) >= min_distance]


def choose_start_locations(rng, min_distance: int = MIN_START_DISTANCE) -> Tuple[str, str]:
    return rng.choice(far_apart_pairs(min_distance))


def npc_step(rng, location: str) -> str:
    """Stay put or walk to a connected location, each equally likely."""
    return rng.choice((location,) + TOWN_MAP[location])

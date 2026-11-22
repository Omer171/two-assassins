# Two Assassins

A 2-player, turn-based, hidden-information game for the terminal. Each player is an assassin
disguised as a townsperson in a medieval town. Both players share one computer and pass it back
and forth. Each turn you get 3 action points to move, question townsfolk, hide, bribe, change
disguise or lay false trails. NPC clues are delayed and fuzzy, and some are lies. Accuse the right
person at your location to win. If nobody is unmasked by dawn (turn 30), the player with more
true clues wins. At the end a replay shows where both players were every turn and which clues
were true.

The full rules are in [spec.md](spec.md); the original requirements are in [problem.md](problem.md).

Needs Python 3.9+. The game uses only the standard library: no network, API key or account.

## Setup (Git Bash, fresh clone)

```bash
git clone https://github.com/Omer171/two-assassins.git
cd two-assassins
python -m venv .venv
source .venv/Scripts/activate        # on macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements-dev.txt
```

## Play

```bash
python -m two_assassins              # random game
python -m two_assassins --seed 42    # repeatable game
```

Commands during your turn (AP cost in brackets):

| Command      | Action                                                        |
|--------------|---------------------------------------------------------------|
| `m <place>`  | move to a connected place (1); a unique prefix works, e.g. `m tav` |
| `a <#>`      | ask a person here what they saw (1)                           |
| `h`          | hide until your next turn (2)                                  |
| `b <#>`      | bribe a person here to lie about you to the next asker (2)     |
| `d`          | change your disguise color (2)                                 |
| `f <place>`  | leave a false trail at a place you have never visited (1)      |
| `x <#>`      | accuse a person here of being the other assassin (1)           |
| `e`          | end your turn                                                  |
| `?` / `q`    | help / quit                                                    |

At the end, the replay is printed and saved to `last_replay.jsonl` (ignored by git).

## How to win

There are two ways the game ends:

1. **Unmask the rival.** If you're at the same place as the other assassin, `x <#>` the
   right person and you win on the spot. You get one accusation per turn.
2. **Dawn.** After turn 30 (15 turns each), the player who collected more **true clues**
   wins. A tie is a draw. True clues are NPC reports of real sightings. Bribed lies and
   false-trail items don't count.

Tips:

- **A wrong accusation is costly.** The rival is told where you are, and that tip counts
  as a true clue for *them*. Only accuse when your clues point to this place.
- Clues are delayed. "Seen at the well 2 turns ago" means the rival *was* there, so think
  about where they could have moved since.
- Asking more townsfolk can raise your dawn score (if they aren't lying), but it uses AP you could spend moving or
  hiding. Hiding stops townsfolk from noticing you until your next turn.
- Change your disguise when you think you've been seen, because old clues describe your
  old color.

## Test

```bash
python -m pytest
```

The tests cover the game logic only (`two_assassins/town.py`, `clues.py`, `game.py`,
`replay.py`). Each test name contains its requirement ID, e.g. `test_r4_...`. The terminal output
in `two_assassins/cli.py` is not tested.

## Layout

```
two_assassins/town.py     R1 map, distances, NPC movement
two_assassins/clues.py    R4 sightings, clues and bribed lies
two_assassins/game.py     Game rules (R1-R7), PlayerView (R2), replay data (R8)
two_assassins/replay.py   R8 JSONL save/load
two_assassins/cli.py      terminal input/output only
tests/                    pytest tests, one file per requirement
docs/decisions/           architecture decision records
```

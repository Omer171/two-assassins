# Two Assassins: Specification (round 1)

Two Assassins is a game for 2 players who take turns on one computer in the terminal ("hot seat").
Each player is an assassin disguised as a townsperson in a medieval town, and each tries to unmask
the other. This spec turns the requirements R1-R8 in `problem.md` into exact rules.

## Constraints

- Python 3.9, standard library only for the game. pytest is used only for tests.
- Starts with one command: `python -m two_assassins` (optionally with `--seed N`).
- No network, API key, login, or paid service.
- The game logic (package `two_assassins`, modules `town`, `clues`, `game`, `replay`) never prints
  or reads input. All terminal I/O is in `two_assassins/cli.py`.
- All randomness comes from one `random.Random(seed)` owned by the `Game`, so a seed always
  replays the same game.

## R1: Town, NPCs, starting positions

- The town map is fixed: 10 locations, connected both ways:

  | Location   | Connected to                      |
  |------------|-----------------------------------|
  | gates      | market, graveyard, stables        |
  | market     | gates, well, tavern, blacksmith   |
  | well       | market, church, tavern            |
  | church     | well, graveyard, castle           |
  | graveyard  | gates, church                     |
  | tavern     | market, well, docks               |
  | blacksmith | market, docks, stables            |
  | docks      | tavern, blacksmith, castle        |
  | castle     | church, docks                     |
  | stables    | gates, blacksmith                 |

- There are 14 NPCs by default, each placed at a random location. Each NPC has an
  appearance: a color (red, blue, green, brown, grey, black, yellow, white) and a garment
  (hood, cloak, apron, tunic, hat).
- At the end of every turn each NPC moves at random: it stays put or goes to a connected
  location, each choice equally likely.
- The two players start in different random locations at least 3 steps apart (shortest path).
- Each player starts with a random disguise taken from the same pool of appearances as the NPCs.
- Every person (NPC or player) has a "cover number" (#1..#16, shuffled), so a player cannot be
  told apart from NPCs by their number.

## R2: Turns and what each player can see

- Player 1 (internally 0) takes turn 1, Player 2 takes turn 2, and so on, alternating.
- Between turns the terminal clears and shows a "pass the device" screen, and waits for Enter.
- During a turn the player sees only `Game.view()`, a `PlayerView` holding: the turn number,
  the AP left, their own location and its connections, their own disguise and hidden status, the
  people at their location (cover number + appearance only), their own clues (text, location,
  color and reported age, but not whether a clue is true), and the places a false trail can be
  left. The view never holds the other player's location. If the other player is at the same
  location, they appear in the people list exactly like an NPC.

## R3: Action points

- Each turn starts with 3 AP. Costs:

  | Action      | AP | Effect                                                          |
  |-------------|----|-----------------------------------------------------------------|
  | move        | 1  | go to a connected location                                      |
  | ask         | 1  | ask a person at your location what they saw (R4)                |
  | hide        | 2  | NPCs do not notice you until your next turn starts             |
  | bribe       | 2  | a person at your location lies to the next person asking about you (R5) |
  | disguise    | 2  | your disguise changes to a different color (R5)                 |
  | false trail | 1  | drop an item at a location you have never been (R5)             |
  | accuse      | 1  | accuse a person at your location (R6), at most once per turn    |

- Ending your turn costs nothing. You cannot take an action that costs more AP than you have
  left. In the terminal, your turn ends automatically when you reach 0 AP.
- Moving after hiding cancels the hiding.

## R4: Delayed, inexact clues

- NPCs remember sightings `(turn, location, player, color)`. An NPC sees a player who is not
  hidden at its location (a) when that player moves into the location, and (b) at the end of
  every turn, for both players.
- When you ask an NPC, it reports on the other player only. It picks one of its sightings from
  1-3 turns ago, at random. Sightings from the current turn are never reported (the clue is
  always delayed), and sightings more than 3 turns old are forgotten.
- The location in the clue is the one where the sighting happened. The reported age is the true
  age +/- 1 (at least 1). The appearance is reported by color only, e.g.
  `#7 says: "Someone in red passed the well about 2 turns ago."`
- If the NPC has no sighting it can report, it says it saw nothing and no clue is recorded.
- If you ask the other player (unknowingly), they answer like an NPC that saw nothing.

## R5: Tricks

- **Bribe**: the person you bribe lies the next time the other player asks them. The lie looks
  like a normal clue, but its location is one where you were *not* at the claimed time, and its
  color is your disguise color at the moment of the bribe. Each bribe fools one ask. Bribing the
  other player has no effect, and the message you get is the same as for an NPC.
- **Disguise**: your disguise gets a new random color (different from the current one) and a
  random garment. Old clues mention your old color.
- **False trail**: pick a location you have never visited. A dropped item (dagger, glove,
  coin purse, torn scarf) is placed there. When the other player moves into that location, or
  starts a turn there, they find it and get a clue pointing at that location with your current
  color. That clue is false. The item is then removed.

## R6: Accusations

- You choose a cover number from the people at your location. Costs 1 AP, at most once per turn.
- If it is the other player, you win right away.
- If it is wrong, the game goes on, and the other player gets a (true) clue telling them where
  you were when you accused.

## R7: Dawn and scoring

- The game lasts 30 turns in total (15 per player). After turn 30 it is dawn and the game ends.
- Score = how many true clues a player received. True clues are NPC clues based on real
  sightings and the reveals after a wrong accusation. Bribed lies and false-trail items are not
  true.
- The higher score wins. A tie is a draw.

## R8: Replay

- `Game.replay()` returns a JSON-ready dict: seed, map, starting locations, one record per
  turn (who played, their actions, both players' locations, hidden flags and disguise colors
  at the end of the turn, and the distance between them), every clue with its `is_true` flag and
  source, and the result (winner, reason, scores).
- At the end of a game, the terminal prints the replay and saves it as `last_replay.jsonl`
  (one JSON object per line: `meta`, then `turn` lines, then `clue` lines, then `result`).

## Module layout

- `two_assassins/town.py`: R1 map, distances, start choice, NPC step
- `two_assassins/clues.py`: R4 sightings and clue/lie generation
- `two_assassins/game.py`: `Game` (R1-R7 rules), `PlayerView`, `replay()` (R8 data)
- `two_assassins/replay.py`: R8 JSONL write/read
- `two_assassins/cli.py`: terminal I/O only (not tested)

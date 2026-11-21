# CLAUDE.md

Two Assassins: a 2-player hot-seat terminal game. The rules are in `spec.md` (requirements: `problem.md`).

- Python 3.9. The game uses the standard library only; pytest is a dev dependency only.
- Run: `python -m two_assassins [--seed N]`. Test: `python -m pytest`.
- No network, API keys, logins, or paid services.
- Logic modules (`town`, `clues`, `game`, `replay`) must never print or read input. Terminal I/O
  belongs in `cli.py` only, which is not unit-tested.
- All randomness goes through the `Game`'s seeded `random.Random`. Never use the `random` module-level functions.
- Every test name contains its requirement ID, e.g. `test_r4_...`.
- Commit in small steps with messages that say what changed and why. Never amend or undo commits.

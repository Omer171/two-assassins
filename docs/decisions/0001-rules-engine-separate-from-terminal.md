# 0001: Game rules in a pure engine, separate from terminal I/O

- Status: accepted
- Date: 2026-11-21

## Decision (Y-statement)

In the context of **a hot-seat terminal game where the fun depends on each player seeing only
their own information (R2)**,
facing **the need to test every rule (R1-R8) repeatably without testing screen output, and to
make sure the rival's location can never leak onto the screen**,
we decided for **a pure `Game` engine (no print/input, one seeded `random.Random`) that exposes
the state of the turn only through an immutable `PlayerView`, plus a thin `cli.py` that only
renders views and parses commands**,
and neglected **a single script that mixes input/output with the rules, and a curses-based UI**,
to achieve **deterministic pytest tests for each requirement, and information hiding enforced by
the API (the view has no field for the rival's position, and the rival shows up like any NPC)**,
accepting **some extra code (view dataclasses, string messages returned by actions) and tests that
set engine state directly, which ties them to internal field names**.

## Notes

- curses is not available in the standard library on Windows, and the game must run in Git Bash.
- Action methods return messages instead of printing them, so a different front end (e.g. a GUI)
  could reuse the engine unchanged.

"""Terminal front end. All printing and input lives here; the rules live in game.py."""
import argparse
import sys

from .game import AP_COSTS, ActionError, Game
from .replay import write_jsonl
from .town import LOCATIONS

REPLAY_FILE = "last_replay.jsonl"
CLEAR = "\033[2J\033[H" + "\n" * 60   # ANSI clear, plus newlines for terminals that ignore it

HELP = """Actions (AP cost):
  m <place>   move to a connected place ({move})
  a <#>       ask a person here what they have seen ({ask})
  h           hide: townsfolk won't notice you until your next turn ({hide})
  b <#>       bribe a person here to lie about you to the next asker ({bribe})
  d           change your disguise to a new color ({disguise})
  f <place>   leave a false trail at a place you have never been ({false_trail})
  x <#>       accuse a person here of being the other assassin ({accuse})
  e           end your turn
  ?           show this help
  q           quit""".format(**AP_COSTS)


def player_name(pid):
    return "Player %d" % (pid + 1)


def resolve_place(text):
    text = text.strip().lower()
    matches = [loc for loc in LOCATIONS if loc.startswith(text)] if text else []
    if text in LOCATIONS:
        return text
    if len(matches) == 1:
        return matches[0]
    raise ActionError("Unknown or ambiguous place %r." % text)


def resolve_number(text):
    try:
        return int(text.strip().lstrip("#"))
    except ValueError:
        raise ActionError("Give a person's number, e.g. 'a 7'.")


def run_command(game, line):
    """Apply one typed command. Returns (message, turn_ended)."""
    cmd, _, arg = line.strip().partition(" ")
    cmd = cmd.lower()
    if cmd == "m":
        return game.move(resolve_place(arg)), False
    if cmd == "a":
        return game.ask(resolve_number(arg)), False
    if cmd == "h":
        return game.hide(), False
    if cmd == "b":
        return game.bribe(resolve_number(arg)), False
    if cmd == "d":
        return game.disguise(), False
    if cmd == "f":
        return game.false_trail(resolve_place(arg)), False
    if cmd == "x":
        return game.accuse(resolve_number(arg)), False
    if cmd == "e":
        return game.end_turn(), True
    if cmd in ("?", "help"):
        return HELP, False
    raise ActionError("Unknown command. Type ? for help.")


def show_view(view, out):
    out.write("=== %s, turn %d of %d (dawn after turn %d) ===\n"
              % (player_name(view.player), view.turn, view.max_turns, view.max_turns))
    out.write("You are at the %s, disguised in a %s%s.\n"
              % (view.location, view.disguise, " (hidden)" if view.hidden else ""))
    out.write("Paths lead to: %s\n" % ", ".join(view.neighbors))
    if view.people_here:
        out.write("People here: %s\n" % ", ".join(
            "#%d (%s)" % (p.cover_id, p.appearance) for p in view.people_here))
    else:
        out.write("Nobody else is here.\n")
    out.write("Your clues:\n")
    if not view.clues:
        out.write("  (none yet)\n")
    for c in view.clues:
        new = " NEW" if c.turn_received >= view.turn - 1 else ""
        out.write("  [turn %d%s] %s\n" % (c.turn_received, new, c.text))
    out.write("AP left: %d%s\n" % (view.ap, "" if view.can_accuse else " (already accused)"))


def handoff(game, inp, out):
    out.write(CLEAR)
    out.write("Pass the device to %s. No peeking, %s!\n"
              % (player_name(game.current), player_name(1 - game.current)))
    inp("Press Enter when %s is ready... " % player_name(game.current))
    out.write(CLEAR)


def format_replay(data):
    names = ("P1", "P2")
    lines = ["", "=" * 70, "REPLAY", "=" * 70, "Town map:"]
    for loc, links in data["map"].items():
        lines.append("  %-10s -> %s" % (loc, ", ".join(links)))
    lines.append("Start: P1 at %s, P2 at %s" % tuple(data["start"]))
    lines.append("")
    lines.append("%-5s %-4s %-12s %-12s %-5s %s" % ("Turn", "Who", "P1 at", "P2 at", "Dist",
                                                 "Actions"))
    for t in data["turns"]:
        at = ["%s%s" % (pos, "*" if hid else "") for pos, hid in zip(t["positions"], t["hidden"])]
        lines.append("%-5d %-4s %-12s %-12s %-5d %s" % (
            t["turn"], names[t["player"]], at[0], at[1], t["distance"],
            "; ".join(t["actions"]) or "-"))
    lines.append("(* = hidden)")
    if data["turns"]:
        closest = min(data["turns"], key=lambda t: t["distance"])
        lines.append("Closest: %d step(s) apart on turn %d." % (closest["distance"],
                                                              closest["turn"]))
    lines.append("")
    lines.append("Clues:")
    if not data["clues"]:
        lines.append("  (none)")
    for c in data["clues"]:
        label = "TRUE" if c["is_true"] else "LIE (%s)" % c["source"]
        lines.append("  %s turn %d [%s] %s" % (names[c["receiver"]], c["turn_received"],
                                               label, c["text"]))
    result = data["result"]
    lines.append("")
    lines.append("True clues: P1 %d, P2 %d" % tuple(result["scores"]))
    if result["winner"] is None:
        lines.append("Result: draw at dawn.")
    else:
        how = "by unmasking the rival" if result["reason"] == "accusation" else "at dawn on clues"
        lines.append("Result: %s wins %s." % (names[result["winner"]], how))
    return "\n".join(lines) + "\n"


def play(game, inp=input, out=sys.stdout):
    out.write("Two Assassins. Two killers hide in a medieval town. Unmask the other before dawn.\n")
    out.write(HELP + "\n")
    while not game.over:
        try:
            handoff(game, inp, out)
        except EOFError:
            out.write("Game abandoned.\n")
            return None
        message = ""   # end_turn's text is for the next player; their clues list shows it
        turn_over = False
        while not turn_over and not game.over:
            show_view(game.view(), out)
            if message:
                out.write(">> %s\n" % message)
            try:
                line = inp("> ")
            except EOFError:
                line = "q"
            if line.strip().lower() == "q":
                out.write("Game abandoned.\n")
                return None
            try:
                message, turn_over = run_command(game, line)
            except ActionError as err:
                message = "Not allowed: %s" % err
                continue
            if not turn_over and not game.over and game.ap == 0:
                out.write(">> %s\n" % message)
                inp("Out of AP. Press Enter to end your turn... ")
                game.end_turn()
                turn_over = True
            out.write("\n")
        if game.over and message:
            out.write(">> %s\n" % message)
    data = game.replay()
    out.write(format_replay(data))
    write_jsonl(data, REPLAY_FILE)
    out.write("Replay saved to %s\n" % REPLAY_FILE)
    return data


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m two_assassins", description=__doc__)
    parser.add_argument("--seed", type=int, default=None, help="seed for a repeatable game")
    args = parser.parse_args(argv)
    try:
        sys.stdout.reconfigure(line_buffering=True)   # prompts show up in Git Bash/mintty
    except AttributeError:
        pass
    try:
        play(Game(seed=args.seed))
    except KeyboardInterrupt:
        print("\nGame abandoned.")
    return 0

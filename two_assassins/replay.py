"""R8: save and load replay data as JSON Lines (one JSON object per line)."""
import json


def write_jsonl(replay: dict, path) -> None:
    meta = {k: replay[k] for k in ("seed", "max_turns", "map", "start")}
    lines = [dict(type="meta", **meta)]
    lines += [dict(type="turn", **t) for t in replay["turns"]]
    lines += [dict(type="clue", **c) for c in replay["clues"]]
    lines.append(dict(type="result", **replay["result"]))
    with open(path, "w", encoding="utf-8") as out:
        for line in lines:
            out.write(json.dumps(line) + "\n")


def read_jsonl(path) -> dict:
    replay = {"turns": [], "clues": []}
    with open(path, encoding="utf-8") as src:
        for raw in src:
            record = json.loads(raw)
            kind = record.pop("type")
            if kind == "meta":
                replay.update(record)
            elif kind == "turn":
                replay["turns"].append(record)
            elif kind == "clue":
                replay["clues"].append(record)
            elif kind == "result":
                replay["result"] = record
    return replay

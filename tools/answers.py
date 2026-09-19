#!/usr/bin/env python3
"""Encode or decode the base64 answers stored in a workbook's exercises.json.

    python3 tools/answers.py encode 'print(x)'          # -> base64
    python3 tools/answers.py encode - < answer.py       # from stdin
    python3 tools/answers.py decode 'cHJpbnQoeCk='      # -> text
    python3 tools/answers.py show workbooks/lecture-04  # print every answer
"""
import base64
import json
import pathlib
import sys


def encode(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def decode(text: str) -> str:
    return base64.b64decode("".join(text.split())).decode("utf-8")


def main(argv):
    if len(argv) < 2 or argv[0] not in {"encode", "decode", "show"}:
        print(__doc__)
        return 2
    command, arg = argv[0], argv[1]
    if command == "show":
        path = pathlib.Path(arg)
        if path.is_dir():
            path = path / "exercises.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        for eid, spec in data["exercises"].items():
            if "answer" in spec:
                print(f"=== {eid} ({spec.get('type')}, {spec.get('xp', '?')} XP)")
                print(decode(spec["answer"]))
                print()
        return 0
    text = sys.stdin.read() if arg == "-" else arg
    print(encode(text) if command == "encode" else decode(text), end="" if command == "decode" else "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

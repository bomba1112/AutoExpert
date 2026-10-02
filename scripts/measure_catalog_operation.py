"""Measure a named local batch operation; never record command arguments or environment."""

import argparse
import json
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ledger", required=True)
    p.add_argument("--operation", required=True)
    p.add_argument("command", nargs=argparse.REMAINDER)
    args = p.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    started = datetime.now(UTC).isoformat()
    tick = time.perf_counter()
    result = subprocess.run(command, check=False)
    seconds = time.perf_counter() - tick
    ledger = Path(args.ledger)
    rows = json.loads(ledger.read_text(encoding="utf-8")) if ledger.exists() else []
    item = dict(
        operation=args.operation,
        mode="PROGRAMMATIC",
        started_at=started,
        ended_at=datetime.now(UTC).isoformat(),
        wall_seconds=round(seconds, 3),
        exit_code=result.returncode,
    )
    rows.append(item)
    ledger.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(item), flush=True)
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()

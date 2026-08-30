from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

try:
    from scripts import python_function_profile as p2
except ModuleNotFoundError:  # assignment-runner image copies modules into /opt/thebitlab
    import python_function_profile as p2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TheBitLab Python function worker")
    parser.add_argument("--source", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        request = json.load(sys.stdin)
        result = p2.execute_worker_request(request, args.source)
        result = p2.validate_worker_result(result)
    except (OSError, json.JSONDecodeError, p2.FunctionProfileError) as error:
        print(
            json.dumps(
                {
                    "schema_version": p2.WORKER_SCHEMA,
                    "status": "worker-error",
                    "stdout": "",
                    "stderr": str(error)[: p2.MAX_STRING_CHARS],
                },
                ensure_ascii=False,
            )
        )
        return 2
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

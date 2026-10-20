#!/usr/bin/env python3
"""Compatibility entry point: install this project first, then run from any directory."""

def main(argv=None):
    try:
        from holden_wip.binary_diff import main as run
    except ModuleNotFoundError as exc:
        if exc.name not in {"holden_wip", "holden_wip.binary_diff"}:
            raise
        import sys
        print("error: install this project first: python -m pip install .", file=sys.stderr)
        return 2
    return run(argv)

if __name__ == "__main__":
    raise SystemExit(main())

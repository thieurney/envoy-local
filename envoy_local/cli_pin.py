"""CLI entry-point for the pin/unpin commands."""

from __future__ import annotations

import argparse
import sys

from envoy_local.env_file import EnvFile
from envoy_local.pin_engine import PinEngine


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy pin",
        description="Pin or unpin keys in a .env file to prevent accidental overwrite.",
    )
    parser.add_argument("env_file", help="Path to the .env file")
    parser.add_argument(
        "keys",
        nargs="+",
        help="Key name(s) to pin or unpin",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--unpin",
        action="store_true",
        default=False,
        help="Remove pin marker instead of adding it",
    )
    mode.add_argument(
        "--list",
        action="store_true",
        default=False,
        help="List all currently pinned keys and exit",
    )
    return parser


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    env = EnvFile(args.env_file)
    env.load()
    engine = PinEngine(env)

    if args.list:
        pinned = engine.list_pinned()
        if pinned:
            for key in pinned:
                print(key)
        else:
            print("No pinned keys.")
        return 0

    if args.unpin:
        result = engine.unpin(args.keys)
        action = "unpinned"
    else:
        result = engine.pin(args.keys)
        action = "pinned"

    if not result.success:
        print(f"Error: {result.error}", file=sys.stderr)
        return 1

    print(result.summary())
    if result.skipped:
        print(f"Keys not found (skipped): {', '.join(result.skipped)}", file=sys.stderr)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(run())

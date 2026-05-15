"""CLI entry-point for the filter sub-command."""
from __future__ import annotations

import argparse
import sys

from envoy_local.env_file import EnvFile
from envoy_local.filter_engine import FilterEngine


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy filter",
        description="Filter keys in a .env file by pattern or prefix.",
    )
    parser.add_argument("env_file", help="Path to the .env file.")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--pattern", metavar="REGEX", help="Regex pattern to match key names.")
    group.add_argument("--prefix", metavar="PREFIX", help="Prefix to match key names.")

    parser.add_argument(
        "--invert",
        action="store_true",
        default=False,
        help="Invert the filter (exclude matching keys).",
    )
    parser.add_argument(
        "--show-excluded",
        action="store_true",
        default=False,
        help="Also print excluded keys.",
    )
    return parser


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    env = EnvFile(args.env_file)
    env.load()
    engine = FilterEngine(env)

    if args.pattern is not None:
        result = engine.by_pattern(args.pattern, invert=args.invert)
    else:
        result = engine.by_prefix(args.prefix, invert=args.invert)

    if not result.success:
        print(f"Error: {result.error}", file=sys.stderr)
        return 1

    print(result.summary())
    print("\nMatched keys:")
    for key, value in result.matched.items():
        print(f"  {key}={value}")

    if args.show_excluded:
        print("\nExcluded keys:")
        for key, value in result.excluded.items():
            print(f"  {key}={value}")

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(run())

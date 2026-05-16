"""CLI entry-point for the flatten command."""
from __future__ import annotations

import argparse
import sys

from envoy_local.env_file import EnvFile
from envoy_local.flatten_engine import FlattenEngine


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy flatten",
        description="Flatten nested env var prefixes into a single level.",
    )
    parser.add_argument("env_file", help="Path to the .env file to flatten.")
    parser.add_argument(
        "--prefix",
        default=None,
        help="Only flatten keys that start with this prefix.",
    )
    parser.add_argument(
        "--keep-prefix",
        action="store_true",
        default=False,
        help="Retain the prefix in the output key names.",
    )
    parser.add_argument(
        "--separator",
        default="__",
        help="Separator used to detect nesting (default: '__').",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Preview changes without writing to disk.",
    )
    return parser


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        env = EnvFile(args.env_file)
        env.load()
    except FileNotFoundError:
        print(f"Error: file not found: {args.env_file}", file=sys.stderr)
        return 1

    engine = FlattenEngine(separator=args.separator)
    result = engine.flatten(
        env,
        prefix=args.prefix,
        strip_prefix=not args.keep_prefix,
        dry_run=args.dry_run,
    )

    if not result.success:
        print(f"Error: {result.error}", file=sys.stderr)
        return 1

    print(result.summary)
    if args.dry_run and result.flattened:
        print("Preview of flattened keys:")
        for key, value in result.flattened.items():
            print(f"  {key}={value}")

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(run())

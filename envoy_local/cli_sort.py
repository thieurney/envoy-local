"""CLI interface for the sort command."""

from __future__ import annotations

import argparse
import sys

from envoy_local.env_file import EnvFile
from envoy_local.sort_engine import SortEngine, SortOrder


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy sort",
        description="Sort keys in a .env file alphabetically or by length.",
    )
    parser.add_argument("env_file", help="Path to the .env file to sort.")
    parser.add_argument(
        "--order",
        choices=[o.value for o in SortOrder],
        default=SortOrder.ALPHA_ASC.value,
        help="Sort order (default: asc).",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        default=False,
        help="Write sorted result back to file (default: dry-run).",
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
    except Exception as exc:  # pragma: no cover
        print(f"Error loading file: {exc}", file=sys.stderr)
        return 1

    order = SortOrder(args.order)
    engine = SortEngine(env)
    result = engine.sort(order=order, dry_run=not args.write)

    if not result.success:
        print(f"Error: {result.error}", file=sys.stderr)
        return 1

    print(result.summary())

    if result.changed and not args.write:
        print("Tip: pass --write to apply changes.")

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(run())

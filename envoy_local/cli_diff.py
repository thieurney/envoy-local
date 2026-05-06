"""CLI command for diffing two .env files using DiffEngine."""

import argparse
import sys

from envoy_local.diff_engine import DiffEngine
from envoy_local.env_file import EnvFile


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy-diff",
        description="Compare two .env files and show differences.",
    )
    parser.add_argument("base", help="Path to the base .env file")
    parser.add_argument("target", help="Path to the target .env file")
    parser.add_argument(
        "--no-mask",
        action="store_true",
        default=False,
        help="Disable secret masking in output (use with caution)",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        default=False,
        help="Print only a change summary instead of full diff",
    )
    return parser


def run(argv=None) -> int:
    """Entry point for the diff CLI command. Returns exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    base_ef = EnvFile(args.base)
    target_ef = EnvFile(args.target)

    try:
        base_ef.load()
    except FileNotFoundError:
        print(f"Error: base file not found: {args.base}", file=sys.stderr)
        return 1

    try:
        target_ef.load()
    except FileNotFoundError:
        print(f"Error: target file not found: {args.target}", file=sys.stderr)
        return 1

    engine = DiffEngine(mask_secrets=not args.no_mask)
    result = engine.compare(base_ef, target_ef)

    print(f"Comparing: {args.base}  →  {args.target}")
    print("-" * 48)

    if args.summary:
        print(result.summary())
    else:
        print(engine.format_diff(result))
        print()
        print(result.summary())

    return 0 if not result.has_changes else 2


if __name__ == "__main__":
    sys.exit(run())

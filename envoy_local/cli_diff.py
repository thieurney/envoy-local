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


def _load_env_file(path: str, label: str) -> tuple["EnvFile | None", int]:
    """Load an EnvFile from *path*, printing a friendly error on failure.

    Returns a ``(env_file, exit_code)`` tuple.  On success *exit_code* is 0
    and *env_file* is the loaded :class:`EnvFile`.  On failure *exit_code* is
    1 and *env_file* is ``None``.
    """
    ef = EnvFile(path)
    try:
        ef.load()
    except FileNotFoundError:
        print(f"Error: {label} file not found: {path}", file=sys.stderr)
        return None, 1
    return ef, 0


def run(argv=None) -> int:
    """Entry point for the diff CLI command. Returns exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    base_ef, code = _load_env_file(args.base, "base")
    if code:
        return code

    target_ef, code = _load_env_file(args.target, "target")
    if code:
        return code

    engine = DiffEngine(mask_secrets=not args.no_mask)
    result = engine.compare(base_ef, target_ef)

    print(f"Comparing: {args.base}  \u2192  {args.target}")
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

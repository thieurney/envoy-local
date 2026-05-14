"""CLI entry-point for the inject command."""
from __future__ import annotations

import argparse
import sys

from envoy_local.env_file import EnvFile
from envoy_local.inject_engine import InjectEngine


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy inject",
        description="Inject variables from a .env file into a subprocess or print export statements.",
    )
    parser.add_argument("env_file", help="Path to the .env file")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite variables already present in the environment",
    )
    parser.add_argument(
        "--export",
        action="store_true",
        default=False,
        help="Print shell export statements instead of injecting into the process",
    )
    parser.add_argument(
        "--mask-secrets",
        action="store_true",
        default=False,
        help="Mask secret values in export output",
    )
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="Optional command to run with the injected environment",
    )
    return parser


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    env_file = EnvFile(args.env_file)
    env_file.load()
    engine = InjectEngine()

    if args.export:
        print(engine.export_shell(env_file, mask_secrets=args.mask_secrets))
        return 0

    command = [c for c in (args.command or []) if c != "--"]
    if command:
        proc = engine.run_with_env(env_file, command, overwrite=args.overwrite)
        return proc.returncode

    result = engine.inject(env_file, overwrite=args.overwrite)
    if not result.success:
        print(f"Error: {result.error}", file=sys.stderr)
        return 1
    print(result.summary())
    return 0

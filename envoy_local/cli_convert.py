"""CLI entry point for the convert command."""

from __future__ import annotations

import argparse
import sys

from envoy_local.convert_engine import ConvertEngine, SUPPORTED_FORMATS
from envoy_local.env_file import EnvFile


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy convert",
        description="Convert a .env file to another format.",
    )
    parser.add_argument("env_file", help="Path to the .env file to convert.")
    parser.add_argument(
        "--format",
        "-f",
        choices=SUPPORTED_FORMATS,
        default="json",
        help="Output format (default: json).",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Write output to this file instead of stdout.",
    )
    return parser


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    env = EnvFile(args.env_file)
    try:
        env.load()
    except FileNotFoundError:
        print(f"Error: file not found: {args.env_file}", file=sys.stderr)
        return 1

    engine = ConvertEngine(env)
    result = engine.convert(args.format)

    if not result.success:
        print(f"Error: {result.error}", file=sys.stderr)
        return 1

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as fh:
                fh.write(result.output)
            print(result.summary())
        except OSError as exc:
            print(f"Error writing output: {exc}", file=sys.stderr)
            return 1
    else:
        print(result.output)

    return 0

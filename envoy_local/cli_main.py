"""Main CLI entry point for envoy-local."""

import argparse
import sys
from envoy_local import cli_diff, cli_sync, cli_export


def build_main_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy",
        description="envoy-local: manage .env files across projects with secret masking.",
    )
    parser.add_argument(
        "--version", action="version", version="%(prog)s 0.1.0"
    )
    subparsers = parser.add_subparsers(dest="command", metavar="<command>")
    subparsers.required = True

    cli_diff.build_parser(subparsers)
    cli_sync.build_parser(subparsers)
    cli_export.build_parser(subparsers)

    return parser


def run(argv=None) -> int:
    parser = build_main_parser()
    args = parser.parse_args(argv)

    dispatch = {
        "diff": cli_diff.run,
        "sync": cli_sync.run,
        "export": cli_export.run,
    }

    handler = dispatch.get(args.command)
    if handler is None:
        parser.print_help()
        return 1

    return handler(args)


if __name__ == "__main__":
    sys.exit(run())

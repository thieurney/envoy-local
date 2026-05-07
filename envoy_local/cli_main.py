"""Main CLI dispatcher for envoy-local."""

from __future__ import annotations

import argparse
import sys


def build_main_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy",
        description="envoy-local: manage .env files across projects.",
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    sub.add_parser("diff", help="Diff two .env files.")
    sub.add_parser("sync", help="Sync .env values to registered projects.")
    sub.add_parser("export", help="Export .env to dotenv or JSON format.")
    sub.add_parser("audit", help="View audit log for a .env file.")
    sub.add_parser("template", help="Render a template using .env values.")
    sub.add_parser("snapshot", help="Create or restore .env snapshots.")
    sub.add_parser("validate", help="Validate a .env file against a schema.")
    sub.add_parser("merge", help="Merge two .env files.")
    sub.add_parser("lint", help="Lint a .env file for common issues.")
    sub.add_parser("encrypt", help="Encrypt secret values in a .env file.")
    sub.add_parser("rotate", help="Rotate secret values in a .env file.")
    sub.add_parser("clone", help="Clone a .env file to a new location.")
    sub.add_parser("watch", help="Watch .env files for changes.")

    return parser


def run(argv: list[str] | None = None) -> None:
    parser = build_main_parser()
    args, remaining = parser.parse_known_args(argv)

    dispatchers = {
        "diff": "envoy_local.cli_diff",
        "sync": "envoy_local.cli_sync",
        "export": "envoy_local.cli_export",
        "audit": "envoy_local.cli_audit",
        "template": "envoy_local.cli_template",
        "snapshot": "envoy_local.cli_snapshot",
        "validate": "envoy_local.cli_validate",
        "merge": "envoy_local.cli_merge",
        "lint": "envoy_local.cli_lint",
        "encrypt": "envoy_local.cli_encrypt",
        "rotate": "envoy_local.cli_rotate",
        "clone": "envoy_local.cli_clone",
        "watch": "envoy_local.cli_watch",
    }

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    module_path = dispatchers.get(args.command)
    if module_path is None:
        parser.error(f"Unknown command: {args.command}")

    import importlib
    module = importlib.import_module(module_path)
    module.run(remaining)

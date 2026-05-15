"""Main CLI dispatcher for envoy-local."""
from __future__ import annotations

import argparse
import sys


def build_main_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy",
        description="envoy-local — manage .env files across projects.",
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    sub.add_parser("diff",      help="Show differences between two .env files.")
    sub.add_parser("sync",      help="Sync keys from a source .env to registered projects.")
    sub.add_parser("export",    help="Export a .env file to dotenv or JSON format.")
    sub.add_parser("audit",     help="View the audit log for a .env file.")
    sub.add_parser("template",  help="Render a template using .env values.")
    sub.add_parser("snapshot",  help="Take or restore a snapshot of a .env file.")
    sub.add_parser("validate",  help="Validate a .env file against a schema.")
    sub.add_parser("merge",     help="Merge two .env files with conflict resolution.")
    sub.add_parser("lint",      help="Lint a .env file for common issues.")
    sub.add_parser("encrypt",   help="Encrypt secret values in a .env file.")
    sub.add_parser("rotate",    help="Rotate secret values in a .env file.")
    sub.add_parser("watch",     help="Watch .env files for changes.")
    sub.add_parser("compare",   help="Compare keys across multiple .env files.")
    sub.add_parser("search",    help="Search for keys or values in .env files.")
    sub.add_parser("rename",    help="Rename a key in a .env file.")
    sub.add_parser("promote",   help="Promote keys from one environment to another.")
    sub.add_parser("convert",   help="Convert a .env file to another format.")
    sub.add_parser("redact",    help="Redact secret values in a .env file.")
    sub.add_parser("strip",     help="Strip comments and blank lines from a .env file.")
    sub.add_parser("pin",       help="Pin or unpin keys in a .env file.")
    sub.add_parser("inject",    help="Inject values into a .env file.")
    sub.add_parser("tag",       help="Tag keys in a .env file.")
    sub.add_parser("archive",   help="Archive a .env file.")
    sub.add_parser("dedupe",    help="Remove duplicate keys from a .env file.")
    sub.add_parser("scope",     help="Scope keys in a .env file by environment.")
    sub.add_parser("group",     help="Group keys in a .env file by prefix.")
    sub.add_parser("filter",    help="Filter keys in a .env file by pattern or prefix.")
    return parser


def run(argv: list[str] | None = None) -> int:  # noqa: C901
    parser = build_main_parser()
    args, remaining = parser.parse_known_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "diff":
        from envoy_local.cli_diff import run as _run
    elif args.command == "sync":
        from envoy_local.cli_sync import run as _run
    elif args.command == "export":
        from envoy_local.cli_export import run as _run
    elif args.command == "audit":
        from envoy_local.cli_audit import run as _run
    elif args.command == "template":
        from envoy_local.cli_template import run as _run
    elif args.command == "snapshot":
        from envoy_local.cli_snapshot import run as _run
    elif args.command == "merge":
        from envoy_local.cli_merge import run as _run
    elif args.command == "encrypt":
        from envoy_local.cli_encrypt import run as _run
    elif args.command == "watch":
        from envoy_local.cli_watch import run as _run
    elif args.command == "compare":
        from envoy_local.cli_compare import run as _run
    elif args.command == "search":
        from envoy_local.cli_search import run as _run
    elif args.command == "redact":
        from envoy_local.cli_redact import run as _run
    elif args.command == "pin":
        from envoy_local.cli_pin import run as _run
    elif args.command == "inject":
        from envoy_local.cli_inject import run as _run
    elif args.command == "tag":
        from envoy_local.cli_tag import run as _run
    elif args.command == "archive":
        from envoy_local.cli_archive import run as _run
    elif args.command == "filter":
        from envoy_local.cli_filter import run as _run
    else:
        print(f"Command '{args.command}' is not yet implemented.", file=sys.stderr)
        return 1

    return _run(remaining)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(run())

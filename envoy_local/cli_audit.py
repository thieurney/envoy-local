"""CLI subcommand for viewing and managing the envoy-local audit log."""

import argparse
import os
from envoy_local.audit_log import AuditLog

DEFAULT_LOG_PATH = os.path.expanduser("~/.envoy_local/audit.json")


def build_parser(subparsers=None) -> argparse.ArgumentParser:
    description = "View or clear the envoy-local audit log"
    if subparsers:
        parser = subparsers.add_parser("audit", help=description)
    else:
        parser = argparse.ArgumentParser(prog="envoy audit", description=description)

    parser.add_argument(
        "--project",
        default=None,
        help="Filter entries by project name",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        default=False,
        help="Clear audit log entries (optionally filtered by --project)",
    )
    parser.add_argument(
        "--log-path",
        default=DEFAULT_LOG_PATH,
        help="Path to audit log file (default: ~/.envoy_local/audit.json)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of entries displayed",
    )
    return parser


def run(args: argparse.Namespace):
    log = AuditLog(log_path=args.log_path)

    if args.clear:
        log.clear(project=args.project)
        scope = f" for project '{args.project}'" if args.project else ""
        print(f"Audit log cleared{scope}.")
        return

    entries = log.entries(project=args.project)

    if not entries:
        scope = f" for project '{args.project}'" if args.project else ""
        print(f"No audit log entries found{scope}.")
        return

    if args.limit:
        entries = entries[-args.limit :]

    for entry in entries:
        print(entry)

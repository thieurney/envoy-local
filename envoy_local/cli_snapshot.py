"""CLI interface for snapshot capture and restore commands."""

from __future__ import annotations

import argparse
from pathlib import Path

from envoy_local.env_file import EnvFile
from envoy_local.snapshot_engine import SnapshotEngine

DEFAULT_STORAGE = Path(".envoy_snapshots.json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy snapshot",
        description="Capture or restore .env file snapshots.",
    )
    parser.add_argument(
        "--storage",
        type=Path,
        default=DEFAULT_STORAGE,
        help="Path to snapshot storage file (default: .envoy_snapshots.json)",
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    capture_p = subparsers.add_parser("capture", help="Capture a snapshot of an env file")
    capture_p.add_argument("project", help="Project name")
    capture_p.add_argument("env_file", type=Path, help="Path to .env file")
    capture_p.add_argument("--label", default=None, help="Optional label for the snapshot")

    list_p = subparsers.add_parser("list", help="List snapshots")
    list_p.add_argument("--project", default=None, help="Filter by project name")

    restore_p = subparsers.add_parser("restore", help="Restore a snapshot")
    restore_p.add_argument("project", help="Project name")
    restore_p.add_argument("timestamp", help="Snapshot timestamp to restore")
    restore_p.add_argument("env_file", type=Path, help="Target .env file to restore into")

    delete_p = subparsers.add_parser("delete", help="Delete a snapshot")
    delete_p.add_argument("project", help="Project name")
    delete_p.add_argument("timestamp", help="Snapshot timestamp to delete")

    return parser


def run(args: argparse.Namespace) -> None:
    engine = SnapshotEngine(storage_path=args.storage)

    if args.subcommand == "capture":
        env = EnvFile(args.env_file)
        env.load()
        snapshot = engine.capture(args.project, env, label=args.label)
        print(f"Captured: {snapshot}")

    elif args.subcommand == "list":
        snapshots = engine.list_snapshots(project=args.project)
        if not snapshots:
            print("No snapshots found.")
        for s in snapshots:
            label_part = f" [{s.label}]" if s.label else ""
            print(f"  {s.project} @ {s.timestamp}{label_part} ({len(s.variables)} vars)")

    elif args.subcommand == "restore":
        matches = [
            s for s in engine.list_snapshots(project=args.project)
            if s.timestamp == args.timestamp
        ]
        if not matches:
            print(f"No snapshot found for project={args.project!r} at {args.timestamp}")
            return
        env = EnvFile(args.env_file)
        env.load()
        engine.restore(matches[0], env)
        print(f"Restored {len(matches[0].variables)} variables to {args.env_file}")

    elif args.subcommand == "delete":
        removed = engine.delete(args.project, args.timestamp)
        if removed:
            print(f"Deleted snapshot for {args.project!r} at {args.timestamp}")
        else:
            print("Snapshot not found.")

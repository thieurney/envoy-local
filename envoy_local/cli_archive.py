"""CLI interface for the archive command."""

from __future__ import annotations

import argparse
from pathlib import Path

from envoy_local.archive_engine import ArchiveEngine
from envoy_local.env_file import EnvFile


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy archive",
        description="Archive a .env file into a compressed zip with metadata.",
    )
    subparsers = parser.add_subparsers(dest="subcommand")

    # create sub-command
    create_p = subparsers.add_parser("create", help="Create a new archive.")
    create_p.add_argument("env_file", help="Path to the .env file to archive.")
    create_p.add_argument(
        "--storage-dir",
        default=".envoy_archives",
        help="Directory to store archives (default: .envoy_archives).",
    )
    create_p.add_argument(
        "--label",
        default="",
        help="Optional label appended to the archive filename.",
    )

    # list sub-command
    list_p = subparsers.add_parser("list", help="List existing archives.")
    list_p.add_argument(
        "--storage-dir",
        default=".envoy_archives",
        help="Directory containing archives (default: .envoy_archives).",
    )

    # extract sub-command
    extract_p = subparsers.add_parser("extract", help="Extract keys from an archive.")
    extract_p.add_argument("archive", help="Path to the zip archive.")

    return parser


def run(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.subcommand == "create":
        env = EnvFile(args.env_file)
        env.load()
        engine = ArchiveEngine(Path(args.storage_dir))
        result = engine.archive(env, label=args.label)
        print(result.summary())
        if not result.success:
            raise SystemExit(1)

    elif args.subcommand == "list":
        engine = ArchiveEngine(Path(args.storage_dir))
        archives = engine.list_archives()
        if not archives:
            print("No archives found.")
        else:
            for path in archives:
                print(path.name)

    elif args.subcommand == "extract":
        engine = ArchiveEngine(Path(args.archive).parent)
        data = engine.extract(Path(args.archive))
        for k, v in data.items():
            print(f"{k}={v}")

    else:
        parser.print_help()

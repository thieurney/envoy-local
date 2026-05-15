"""CLI interface for the tag engine."""
from __future__ import annotations

import argparse
import sys

from envoy_local.env_file import EnvFile
from envoy_local.tag_engine import TagEngine


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy tag",
        description="Attach or query metadata tags on .env keys.",
    )
    sub = parser.add_subparsers(dest="subcommand", required=True)

    # add
    add_p = sub.add_parser("add", help="Attach a tag to one or more keys")
    add_p.add_argument("env_file", help="Path to the .env file")
    add_p.add_argument("tag", help="Tag label to attach")
    add_p.add_argument("keys", nargs="+", help="Keys to tag")
    add_p.add_argument("--dry-run", action="store_true", default=False)

    # remove
    rm_p = sub.add_parser("remove", help="Remove a tag from one or more keys")
    rm_p.add_argument("env_file", help="Path to the .env file")
    rm_p.add_argument("tag", help="Tag label to remove")
    rm_p.add_argument("keys", nargs="+", help="Keys to untag")
    rm_p.add_argument("--dry-run", action="store_true", default=False)

    # list
    ls_p = sub.add_parser("list", help="List tags for a key, or keys for a tag")
    ls_p.add_argument("env_file", help="Path to the .env file")
    group = ls_p.add_mutually_exclusive_group(required=True)
    group.add_argument("--key", help="Show tags for this key")
    group.add_argument("--tag", help="Show keys carrying this tag")

    return parser


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    env = EnvFile(args.env_file)
    env.load()
    engine = TagEngine(env)

    if args.subcommand == "add":
        result = engine.add_tag(args.keys, args.tag, dry_run=args.dry_run)
        if not result.success:
            print(f"Error: {result.error}", file=sys.stderr)
            return 1
        prefix = "[dry-run] " if args.dry_run else ""
        print(prefix + result.summary())
        return 0

    if args.subcommand == "remove":
        result = engine.remove_tag(args.keys, args.tag, dry_run=args.dry_run)
        if not result.success:
            print(f"Error: {result.error}", file=sys.stderr)
            return 1
        prefix = "[dry-run] " if args.dry_run else ""
        print(prefix + result.summary())
        return 0

    if args.subcommand == "list":
        if args.key:
            tags = engine.tags_for_key(args.key)
            print(f"Tags for '{args.key}': {', '.join(tags) if tags else '(none)'}")
        else:
            keys = engine.keys_for_tag(args.tag)
            print(f"Keys with tag '{args.tag}': {', '.join(keys) if keys else '(none)'}")
        return 0

    return 0

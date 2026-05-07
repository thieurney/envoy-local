"""CLI interface for merging two .env files."""

import argparse
import sys
from pathlib import Path

from envoy_local.env_file import EnvFile
from envoy_local.merge_engine import MergeEngine, MergeStrategy


def build_parser(parent_subparsers=None):
    description = "Merge two .env files with a chosen conflict resolution strategy."
    if parent_subparsers:
        parser = parent_subparsers.add_parser("merge", description=description)
    else:
        parser = argparse.ArgumentParser(description=description)

    parser.add_argument("base", help="Path to the base .env file")
    parser.add_argument("target", help="Path to the target .env file to merge in")
    parser.add_argument(
        "--output", "-o", default=None, help="Write merged result to this file"
    )
    parser.add_argument(
        "--strategy",
        choices=[s.value for s in MergeStrategy],
        default=MergeStrategy.BASE_WINS.value,
        help="Conflict resolution strategy (default: base_wins)",
    )
    parser.add_argument(
        "--show-conflicts", action="store_true", help="Print conflict details"
    )
    return parser


def run(args):
    base_path = Path(args.base)
    target_path = Path(args.target)

    if not base_path.exists():
        print(f"Error: base file not found: {base_path}", file=sys.stderr)
        sys.exit(1)
    if not target_path.exists():
        print(f"Error: target file not found: {target_path}", file=sys.stderr)
        sys.exit(1)

    base_env = EnvFile(base_path)
    base_env.load()
    target_env = EnvFile(target_path)
    target_env.load()

    strategy = MergeStrategy(args.strategy)
    engine = MergeEngine(strategy=strategy)
    result = engine.merge(base_env, target_env)

    print(result.summary())

    if args.show_conflicts and result.conflicts:
        print("\nConflicts:")
        for c in result.conflicts:
            print(f"  {c.key}: base={c.base_value!r}, target={c.target_value!r} -> resolved={c.resolved_value!r}")

    if args.output:
        out_path = Path(args.output)
        merged_env = EnvFile(out_path)
        for k, v in result.merged.items():
            merged_env.set(k, v)
        merged_env.save()
        print(f"Merged file written to {out_path}")

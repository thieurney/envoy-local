"""CLI interface for the sync command."""

import argparse
import sys

from envoy_local.project_registry import ProjectRegistry
from envoy_local.sync_engine import SyncEngine
from envoy_local.secret_mask import SecretMasker


DEFAULT_REGISTRY_PATH = "~/.envoy_local/registry.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy sync",
        description="Sync a source .env file to all registered projects.",
    )
    parser.add_argument("source", help="Path to the source .env file")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Preview changes without writing files",
    )
    parser.add_argument(
        "--registry",
        default=DEFAULT_REGISTRY_PATH,
        help="Path to the project registry JSON file",
    )
    parser.add_argument(
        "--show-secrets",
        action="store_true",
        default=False,
        help="Show secret values instead of masking them",
    )
    return parser


def run(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    registry = ProjectRegistry(args.registry)
    engine = SyncEngine(registry)
    masker = SecretMasker()

    if args.dry_run:
        print(f"[dry-run] Syncing from: {args.source}")
    else:
        print(f"Syncing from: {args.source}")

    report = engine.sync(args.source, dry_run=args.dry_run)

    for result in report.results:
        status = "[skipped]"
        if result.error:
            status = f"[error] {result.error}"
        elif result.applied:
            status = "[synced]"
        elif args.dry_run and result.diff.has_changes:
            status = "[would sync]"

        print(f"  {result.project_name} ({result.project_path}): {status}")

        if result.diff.has_changes and not result.error:
            for key in result.diff.added:
                print(f"    + {key}")
            for key in result.diff.removed:
                print(f"    - {key}")
            for key in result.diff.modified:
                display = "***" if (not args.show_secrets and masker.is_secret(key)) else "changed"
                print(f"    ~ {key}: {display}")

    print()
    print(report.summary())
    return 0 if report.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run())

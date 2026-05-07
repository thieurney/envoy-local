"""Main CLI entry point for envoy-local, dispatching subcommands."""

import argparse
import sys


DESCRIPTION = "envoy-local: Lightweight .env manager with secret masking."


def build_main_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy",
        description=DESCRIPTION,
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    subparsers.required = True

    # diff subcommand
    diff_parser = subparsers.add_parser("diff", help="Show diff between two .env files")
    diff_parser.add_argument("base", help="Base .env file")
    diff_parser.add_argument("target", help="Target .env file")
    diff_parser.add_argument("--show-secrets", action="store_true", default=False)

    # sync subcommand
    sync_parser = subparsers.add_parser("sync", help="Sync source .env to registered projects")
    sync_parser.add_argument("source", help="Source .env file")
    sync_parser.add_argument("--dry-run", action="store_true", default=False)
    sync_parser.add_argument("--registry", default="~/.envoy_local/registry.json")
    sync_parser.add_argument("--show-secrets", action="store_true", default=False)

    # register subcommand
    reg_parser = subparsers.add_parser("register", help="Register a project .env path")
    reg_parser.add_argument("name", help="Project name")
    reg_parser.add_argument("path", help="Path to project .env file")
    reg_parser.add_argument("--registry", default="~/.envoy_local/registry.json")

    # list subcommand
    list_parser = subparsers.add_parser("list", help="List registered projects")
    list_parser.add_argument("--registry", default="~/.envoy_local/registry.json")

    return parser


def run(argv=None) -> int:
    parser = build_main_parser()
    args = parser.parse_args(argv)

    if args.command == "diff":
        from envoy_local.cli_diff import run as diff_run
        return diff_run([args.base, args.target] + (["--show-secrets"] if args.show_secrets else []))

    if args.command == "sync":
        from envoy_local.cli_sync import run as sync_run
        extra = []
        if args.dry_run:
            extra.append("--dry-run")
        if args.show_secrets:
            extra.append("--show-secrets")
        return sync_run([args.source, "--registry", args.registry] + extra)

    if args.command == "register":
        from envoy_local.project_registry import ProjectRegistry
        reg = ProjectRegistry(args.registry)
        reg.register(args.name, args.path)
        print(f"Registered '{args.name}' -> {args.path}")
        return 0

    if args.command == "list":
        from envoy_local.project_registry import ProjectRegistry
        reg = ProjectRegistry(args.registry)
        projects = reg.list_projects()
        if not projects:
            print("No projects registered.")
        for name, info in projects.items():
            print(f"  {name}: {info.get('path', '')}")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(run())

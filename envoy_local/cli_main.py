"""Main CLI entry point for envoy-local."""

import argparse
import sys


def build_main_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy",
        description="Lightweight wrapper to manage .env files across multiple projects.",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    # Register sub-commands lazily to avoid circular imports
    _commands = {
        "diff": "envoy_local.cli_diff",
        "sync": "envoy_local.cli_sync",
        "export": "envoy_local.cli_export",
        "audit": "envoy_local.cli_audit",
        "template": "envoy_local.cli_template",
        "snapshot": "envoy_local.cli_snapshot",
        "merge": "envoy_local.cli_merge",
        "encrypt": "envoy_local.cli_encrypt",
        "watch": "envoy_local.cli_watch",
        "compare": "envoy_local.cli_compare",
        "search": "envoy_local.cli_search",
        "convert": "envoy_local.cli_convert",
        "redact": "envoy_local.cli_redact",
    }

    for name, module_path in _commands.items():
        import importlib
        mod = importlib.import_module(module_path)
        sub = mod.build_parser()
        subparsers.add_parser(
            name,
            parents=[sub],
            add_help=False,
            description=sub.description,
            help=sub.description,
        )

    return parser


def run(argv=None) -> int:
    import importlib

    parser = argparse.ArgumentParser(
        prog="envoy",
        description="Lightweight wrapper to manage .env files across multiple projects.",
    )
    subparsers = parser.add_subparsers(dest="command")
    subparsers.required = True

    _commands = [
        "diff", "sync", "export", "audit", "template", "snapshot",
        "merge", "encrypt", "watch", "compare", "search", "convert", "redact",
    ]
    for name in _commands:
        subparsers.add_parser(name)

    args, remaining = parser.parse_known_args(argv)
    mod = importlib.import_module(f"envoy_local.cli_{args.command}")
    return mod.run(remaining)


if __name__ == "__main__":
    sys.exit(run())

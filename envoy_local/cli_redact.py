"""CLI interface for the redact command."""

import argparse
from envoy_local.env_file import EnvFile
from envoy_local.redact_engine import RedactEngine


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy redact",
        description="Redact specific keys in a .env file by replacing their values.",
    )
    parser.add_argument("env_file", help="Path to the .env file")
    parser.add_argument(
        "keys",
        nargs="*",
        help="Specific key names to redact",
    )
    parser.add_argument(
        "--pattern",
        metavar="PATTERN",
        help="Redact all keys matching this regex pattern (case-insensitive)",
    )
    parser.add_argument(
        "--placeholder",
        default="***REDACTED***",
        help="Value to substitute for redacted keys (default: ***REDACTED***)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Show what would be redacted without writing changes",
    )
    return parser


def run(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    env = EnvFile(args.env_file)
    env.load()

    engine = RedactEngine(placeholder=args.placeholder)
    save = not args.dry_run

    if args.pattern:
        result = engine.redact_pattern(env, args.pattern, save=save)
    elif args.keys:
        result = engine.redact(env, args.keys, save=save)
    else:
        parser.error("Provide at least one KEY or --pattern.")

    print(result.summary)
    if args.dry_run and result.redacted_keys:
        print("[dry-run] Keys that would be redacted:", ", ".join(result.redacted_keys))

    return 0 if result.success else 1

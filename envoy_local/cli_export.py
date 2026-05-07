"""CLI subcommand: export — export a .env file to stdout in a chosen format."""

import argparse
import sys
from envoy_local.env_file import EnvFile
from envoy_local.secret_mask import SecretMasker
from envoy_local.export_engine import ExportEngine, SUPPORTED_FORMATS


def build_parser(subparsers=None) -> argparse.ArgumentParser:
    description = "Export a .env file to dotenv, JSON, or shell format."
    if subparsers is not None:
        parser = subparsers.add_parser("export", help=description)
    else:
        parser = argparse.ArgumentParser(prog="envoy export", description=description)

    parser.add_argument("env_file", help="Path to the .env file to export.")
    parser.add_argument(
        "--format",
        "-f",
        choices=list(SUPPORTED_FORMATS),
        default="dotenv",
        help="Output format (default: dotenv).",
    )
    parser.add_argument(
        "--mask-secrets",
        action="store_true",
        default=False,
        help="Mask secret values before exporting.",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Write output to a file instead of stdout.",
    )
    return parser


def run(args: argparse.Namespace) -> int:
    env = EnvFile(args.env_file)
    try:
        env.load()
    except FileNotFoundError:
        print(f"Error: file not found: {args.env_file}", file=sys.stderr)
        return 1

    engine = ExportEngine(masker=SecretMasker())
    try:
        output = engine.export(env, fmt=args.format, mask_secrets=args.mask_secrets)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(output + "\n")
        print(f"Exported to {args.output}")
    else:
        print(output)

    return 0

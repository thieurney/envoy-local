"""CLI sub-command: envoy template — render a .env template."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envoy_local.env_file import EnvFile
from envoy_local.template_engine import TemplateEngine


def build_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:
    description = "Render a .env.template file using values from a source .env."
    if parent is not None:
        parser = parent.add_parser("template", help=description, description=description)
    else:
        parser = argparse.ArgumentParser(prog="envoy template", description=description)

    parser.add_argument("template", help="Path to the .env.template file")
    parser.add_argument("--values", required=True, help="Path to .env file supplying values")
    parser.add_argument("--output", default=None, help="Write rendered output to this file (default: stdout)")
    parser.add_argument("--strict", action="store_true", default=False,
                        help="Exit with error if any placeholder is unresolved")
    return parser


def run(args: argparse.Namespace) -> int:
    template_path = Path(args.template)
    values_path = Path(args.values)

    if not template_path.exists():
        print(f"Error: template file not found: {template_path}", file=sys.stderr)
        return 1

    if not values_path.exists():
        print(f"Error: values file not found: {values_path}", file=sys.stderr)
        return 1

    env = EnvFile(str(values_path))
    env.load()

    engine = TemplateEngine(strict=args.strict)

    try:
        result = engine.render_from_file(str(template_path), env.all())
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.output:
        Path(args.output).write_text(result.rendered, encoding="utf-8")
        print(f"Rendered to {args.output}")
    else:
        print(result.rendered, end="")

    print(f"# {result.summary()}", file=sys.stderr)
    return 0

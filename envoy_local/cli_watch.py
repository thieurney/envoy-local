"""CLI entry point for the watch command."""

from __future__ import annotations

import argparse
import time

from envoy_local.watch_engine import WatchEngine, WatchEvent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy watch",
        description="Watch .env files for changes and print events.",
    )
    parser.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help="One or more .env files to monitor.",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        metavar="SECONDS",
        help="Polling interval in seconds (default: 2.0).",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Poll once and exit (useful for scripting/testing).",
    )
    return parser


def run(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    engine = WatchEngine()
    for f in args.files:
        engine.register(f)

    def _print_event(event: WatchEvent) -> None:
        print(f"[{event.kind.upper()}] {event.path}")

    engine.on_change(_print_event)

    print(f"Watching {len(args.files)} file(s). Press Ctrl+C to stop.")
    try:
        while True:
            result = engine.poll()
            for err in result.errors:
                print(f"[ERROR] {err}")
            if args.once:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nWatch stopped.")

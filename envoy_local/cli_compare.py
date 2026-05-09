"""CLI interface for comparing two .env files."""
import argparse
import sys
from envoy_local.env_file import EnvFile
from envoy_local.compare_engine import CompareEngine


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy compare",
        description="Compare two .env files and report value drift.",
    )
    parser.add_argument("left", help="Path to the left (base) .env file")
    parser.add_argument("right", help="Path to the right (target) .env file")
    parser.add_argument(
        "--mask-secrets",
        action="store_true",
        default=False,
        help="Mask secret values in output",
    )
    parser.add_argument(
        "--only-diffs",
        action="store_true",
        default=False,
        help="Show only keys that differ",
    )
    return parser


def run(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    left_env = EnvFile(args.left)
    left_env.load()
    right_env = EnvFile(args.right)
    right_env.load()

    engine = CompareEngine(mask_secrets=args.mask_secrets)
    result = engine.compare(
        left_env, right_env,
        left_label=args.left,
        right_label=args.right,
    )

    print(result.summary())
    print()

    for entry in result.entries:
        if args.only_diffs and entry.is_same:
            continue
        lv = entry.left_value if entry.left_value is not None else "<missing>"
        rv = entry.right_value if entry.right_value is not None else "<missing>"
        status_marker = "=" if entry.is_same else "!"
        print(f"  [{status_marker}] {entry.key}: {lv!r} -> {rv!r}")

    return 1 if result.has_differences else 0


if __name__ == "__main__":
    sys.exit(run())

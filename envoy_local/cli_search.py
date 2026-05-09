import argparse
import sys
from pathlib import Path

from envoy_local.env_file import EnvFile
from envoy_local.search_engine import SearchEngine
from envoy_local.secret_mask import SecretMasker


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy search",
        description="Search for keys or values across one or more .env files.",
    )
    parser.add_argument("query", help="Search term or regex pattern")
    parser.add_argument("files", nargs="+", help="One or more .env files to search")
    parser.add_argument(
        "--regex", action="store_true", default=False, help="Treat query as a regex pattern"
    )
    parser.add_argument(
        "--keys-only", action="store_true", default=False, help="Search only in keys"
    )
    parser.add_argument(
        "--values-only", action="store_true", default=False, help="Search only in values"
    )
    parser.add_argument(
        "--case-sensitive", action="store_true", default=False, help="Enable case-sensitive matching"
    )
    parser.add_argument(
        "--mask-secrets", action="store_true", default=False, help="Mask secret values in output"
    )
    return parser


def run(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    search_keys = not args.values_only
    search_values = not args.keys_only

    engine = SearchEngine(
        case_sensitive=args.case_sensitive,
        search_keys=search_keys,
        search_values=search_values,
    )

    masker = SecretMasker() if args.mask_secrets else None

    env_files = []
    for file_path in args.files:
        p = Path(file_path)
        if not p.exists():
            print(f"[error] File not found: {file_path}", file=sys.stderr)
            return 1
        ef = EnvFile(p)
        ef.load()
        env_files.append(ef)

    try:
        result = engine.search(env_files, args.query, use_regex=args.regex)
    except ValueError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    print(result.summary())
    for match in result.matches:
        display_value = masker.mask(match.key, match.value) if masker else match.value
        loc = f":{match.line_number}" if match.line_number is not None else ""
        print(f"  {match.file_path}{loc}  {match.key}={display_value}")

    return 0

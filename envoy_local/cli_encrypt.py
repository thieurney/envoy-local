"""CLI interface for encrypting/decrypting .env file values."""

import argparse
import sys
from pathlib import Path

from envoy_local.encrypt_engine import EncryptEngine
from envoy_local.env_file import EnvFile


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envoy encrypt",
        description="Encrypt or decrypt values in a .env file",
    )
    parser.add_argument("env_file", help="Path to the .env file")
    parser.add_argument(
        "--passphrase", required=True, help="Passphrase used to derive the encryption key"
    )
    subparsers = parser.add_subparsers(dest="action", required=True)

    enc_parser = subparsers.add_parser("encrypt", help="Encrypt values in the file")
    enc_parser.add_argument(
        "--keys", nargs="+", metavar="KEY", help="Specific keys to encrypt (default: all)"
    )
    enc_parser.add_argument(
        "--dry-run", action="store_true", help="Preview without writing changes"
    )

    subparsers.add_parser("decrypt", help="Decrypt and print values to stdout")

    return parser


def run(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    env_path = Path(args.env_file)
    if not env_path.exists():
        print(f"Error: file not found: {env_path}", file=sys.stderr)
        return 1

    env_file = EnvFile(env_path)
    env_file.load()
    engine = EncryptEngine(passphrase=args.passphrase)

    if args.action == "encrypt":
        result = engine.encrypt_file(env_file, keys=getattr(args, "keys", None))
        if not result.success:
            for err in result.errors:
                print(f"Error: {err}", file=sys.stderr)
            return 1
        print(result.summary())
        if not args.dry_run:
            for key, enc_value in result.encrypted.items():
                env_file.set(key, enc_value)
            env_file.save()
            print(f"Saved encrypted values to {env_path}")
        else:
            for key, enc_value in result.encrypted.items():
                print(f"  {key}={enc_value}")
        return 0

    if args.action == "decrypt":
        decrypted = engine.decrypt_file(env_file)
        for key, value in decrypted.items():
            print(f"{key}={value}")
        return 0

    return 1

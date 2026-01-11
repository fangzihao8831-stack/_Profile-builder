#!/usr/bin/env python3
"""
Profile Builder - Browser Profile Warming System

Usage:
    python run.py diagnose                              # Check all connections
    python run.py browse <profile_id> --structure fashion --duration 3
    python run.py browse <profile_id> --debug           # With debug output
"""

import argparse
import re
import sys


def validate_profile_id(profile_id: str) -> bool:
    """Validate profile ID to prevent path traversal and injection attacks."""
    # Only allow alphanumeric, underscore, and hyphen
    if not re.match(r'^[a-zA-Z0-9_-]+$', profile_id):
        return False
    # Prevent path traversal
    if '..' in profile_id or '/' in profile_id or '\\' in profile_id:
        return False
    # Reasonable length limit
    if len(profile_id) > 64:
        return False
    return True


def cmd_diagnose(args):
    """Check all external connections and dependencies."""
    print("Running diagnostics...\n")

    all_ok = True

    # Check AdsPower
    from browser.adspower import check_adspower
    ads_ok, ads_msg = check_adspower()
    if ads_ok:
        print(f"[OK] {ads_msg}")
    else:
        print(f"[FAIL] {ads_msg}")
        all_ok = False

    # Check Ollama
    from ai.ollama_client import check_ollama
    ollama_ok, ollama_msg = check_ollama()
    if ollama_ok:
        print(f"[OK] {ollama_msg}")
    else:
        print(f"[FAIL] {ollama_msg}")
        all_ok = False

    # Check PaddleOCR
    try:
        from paddleocr import PaddleOCR
        print("[OK] PaddleOCR import")
    except ImportError as e:
        print(f"[FAIL] PaddleOCR: {e}")
        all_ok = False

    # Check HumanCursor
    try:
        from humancursor import SystemCursor
        print("[OK] HumanCursor import")
    except ImportError as e:
        print(f"[FAIL] HumanCursor: {e}")
        all_ok = False

    # Check Selenium
    try:
        from selenium import webdriver
        print("[OK] Selenium import")
    except ImportError as e:
        print(f"[FAIL] Selenium: {e}")
        all_ok = False

    print()
    if all_ok:
        print("All systems ready!")
        return 0
    else:
        print("Some checks failed. Please fix issues above.")
        return 1


def cmd_browse(args):
    """Run a browsing session."""
    from ai.session_planner import BrowsingStructure
    from core.session import BrowsingSession

    # Validate profile ID
    if not validate_profile_id(args.profile_id):
        print(f"Error: Invalid profile ID '{args.profile_id}'")
        print("Profile ID must be alphanumeric with hyphens/underscores only, max 64 chars.")
        return 1

    # Parse structure
    try:
        structure = BrowsingStructure(args.structure.lower())
    except ValueError:
        valid = [s.value for s in BrowsingStructure]
        print(f"Error: Invalid structure '{args.structure}'")
        print(f"Valid options: {', '.join(valid)}")
        return 1

    # Create and run session
    print(f"Starting {args.structure} browsing session for profile {args.profile_id}")
    print(f"Duration: {args.duration} minutes")
    print(f"Debug: {args.debug}")
    print()

    session = BrowsingSession(
        profile_id=args.profile_id,
        structure=structure,
        duration_minutes=args.duration,
        debug=args.debug
    )

    success = session.start()
    return 0 if success else 1


def main():
    parser = argparse.ArgumentParser(
        description="Profile Builder - Browser Profile Warming System"
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # diagnose command
    diag_parser = subparsers.add_parser(
        "diagnose",
        help="Check all connections and dependencies"
    )
    diag_parser.set_defaults(func=cmd_diagnose)

    # browse command
    browse_parser = subparsers.add_parser(
        "browse",
        help="Run a browsing session"
    )
    browse_parser.add_argument(
        "profile_id",
        type=str,
        help="AdsPower profile ID"
    )
    browse_parser.add_argument(
        "--structure", "-s",
        type=str,
        default="fashion",
        help="Browsing structure: news, youtube, fashion, forums, shopping (default: fashion)"
    )
    browse_parser.add_argument(
        "--duration", "-d",
        type=int,
        default=3,
        help="Duration in minutes (default: 3)"
    )
    browse_parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output and screenshots"
    )
    browse_parser.set_defaults(func=cmd_browse)

    # Legacy support: --diagnose flag
    parser.add_argument(
        "--diagnose",
        action="store_true",
        help="(legacy) Run diagnostics - use 'diagnose' command instead"
    )

    # Legacy support: --profile flag
    parser.add_argument(
        "--profile",
        type=str,
        help="(legacy) Profile ID - use 'browse <profile>' instead"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=30,
        help="(legacy) Duration in minutes"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="(legacy) Enable debug"
    )

    args = parser.parse_args()

    # Handle legacy --diagnose
    if args.diagnose:
        return cmd_diagnose(args)

    # Handle legacy --profile
    if args.profile:
        # Convert to browse command args
        args.profile_id = args.profile
        args.structure = "fashion"
        return cmd_browse(args)

    # Handle subcommands
    if hasattr(args, 'func'):
        return args.func(args)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())

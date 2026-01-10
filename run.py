#!/usr/bin/env python3
"""
Profile Builder - Browser Profile Warming System

Usage:
    python run.py --diagnose                    # Check all connections
    python run.py --profile ID --duration 30   # Run 30-minute session
    python run.py --profile ID --debug         # Run with debug output
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


def diagnose():
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


def run_session(profile_id: str, duration: int, debug: bool = False):
    """Run a warming session."""
    print(f"Starting session for profile {profile_id}")
    print(f"Duration: {duration} minutes")
    print(f"Debug: {debug}")
    print()
    print("Session not yet implemented. Complete Milestone 1 first.")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Profile Builder - Browser Profile Warming System"
    )

    parser.add_argument(
        "--diagnose",
        action="store_true",
        help="Run diagnostics to check all connections"
    )

    parser.add_argument(
        "--profile",
        type=str,
        help="AdsPower profile ID to use"
    )

    parser.add_argument(
        "--duration",
        type=int,
        default=30,
        help="Session duration in minutes (default: 30)"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug output"
    )

    args = parser.parse_args()

    if args.diagnose:
        return diagnose()

    if args.profile:
        if not validate_profile_id(args.profile):
            print(f"Error: Invalid profile ID '{args.profile}'")
            print("Profile ID must be alphanumeric with hyphens/underscores only, max 64 chars.")
            return 1
        return run_session(args.profile, args.duration, args.debug)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())

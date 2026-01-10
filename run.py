#!/usr/bin/env python3
"""
Profile Builder - Browser Profile Warming System

Usage:
    python run.py --diagnose                    # Check all connections
    python run.py --profile ID --duration 30   # Run 30-minute session
    python run.py --profile ID --debug         # Run with debug output
"""

import argparse
import sys


def diagnose():
    """Check all external connections and dependencies."""
    print("Running diagnostics...\n")

    all_ok = True

    # Check AdsPower
    try:
        import requests
        resp = requests.get("http://local.adspower.net:50325/status", timeout=2)
        if resp.status_code == 200:
            print("[OK] AdsPower connection")
        else:
            print("[FAIL] AdsPower returned status", resp.status_code)
            all_ok = False
    except Exception as e:
        print(f"[FAIL] AdsPower connection: {e}")
        all_ok = False

    # Check Ollama
    try:
        import ollama
        models = ollama.list()
        qwen_found = any("qwen2.5-vl" in m.get("name", "") for m in models.get("models", []))
        if qwen_found:
            print("[OK] Ollama + Qwen2.5-VL")
        else:
            print("[WARN] Ollama OK but qwen2.5-vl:7b not found. Run: ollama pull qwen2.5-vl:7b")
            all_ok = False
    except Exception as e:
        print(f"[FAIL] Ollama connection: {e}")
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
        return run_session(args.profile, args.duration, args.debug)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())

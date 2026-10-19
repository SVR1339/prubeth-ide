#!/usr/bin/env python3
"""
BSVR TECHNOLOGIES — AUTOMATED CONTACT & IDENTITY SYNCHRONIZER
Usage:
  python scripts/update_contact_info.py --email contact@bsvr.work --phone "+918886244999" --github SVR1339
Or run without arguments to enter interactive update mode.
"""

import re
import sys
import argparse
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
INDEX_HTML = ROOT_DIR / "website" / "index.html"

def update_contact(primary_email=None, secondary_email=None, phone=None, github=None, twitter=None, instagram=None):
    if not INDEX_HTML.exists():
        print(f"[!] Error: {INDEX_HTML} not found.")
        return False

    content = INDEX_HTML.read_text(encoding="utf-8")
    changes = 0

    if primary_email:
        # Update mailto and text references
        old_pattern = r'contact@bsvr\.work'
        content = re.sub(r'mailto:[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', f'mailto:{primary_email}', content)
        content = re.sub(r'primaryEmail:\s*["\'][^"\']+["\']', f'primaryEmail: "{primary_email}"', content)
        print(f"[+] Updated primary email to: {primary_email}")
        changes += 1

    if secondary_email:
        content = re.sub(r'secondaryEmail:\s*["\'][^"\']+["\']', f'secondaryEmail: "{secondary_email}"', content)
        print(f"[+] Updated secondary email to: {secondary_email}")
        changes += 1

    if phone:
        clean_phone = re.sub(r'\s+', '', phone)
        content = re.sub(r'tel:\+?[0-9]+', f'tel:{clean_phone}', content)
        content = re.sub(r'directPhone:\s*["\'][^"\']+["\']', f'directPhone: "{clean_phone}"', content)
        print(f"[+] Updated phone to: {phone}")
        changes += 1

    if github:
        content = re.sub(r'github\.com/[a-zA-Z0-9_-]+', f'github.com/{github}', content)
        content = re.sub(r'githubUser:\s*["\'][^"\']+["\']', f'githubUser: "{github}"', content)
        content = re.sub(r'githubUrl:\s*["\'][^"\']+["\']', f'githubUrl: "https://github.com/{github}"', content)
        print(f"[+] Updated GitHub username to: {github}")
        changes += 1

    if twitter:
        handle = twitter.lstrip('@')
        content = re.sub(r'x\.com/[a-zA-Z0-9_]+', f'x.com/{handle}', content)
        content = re.sub(r'twitterHandle:\s*["\'][^"\']+["\']', f'twitterHandle: "{handle}"', content)
        print(f"[+] Updated Twitter/X handle to: @{handle}")
        changes += 1

    if instagram:
        handle = instagram.lstrip('@').strip('/')
        content = re.sub(r'instagram\.com/[a-zA-Z0-9_]+/?(?:\?hl=en/?)?', f'instagram.com/{handle}/', content)
        content = re.sub(r'instagramHandle:\s*["\'][^"\']+["\']', f'instagramHandle: "{handle}"', content)
        print(f"[+] Updated Instagram handle to: @{handle}")
        changes += 1

    if changes > 0:
        INDEX_HTML.write_text(content, encoding="utf-8")
        print(f"\n[SUCCESS] Successfully applied {changes} update(s) to {INDEX_HTML.relative_to(ROOT_DIR)}!")
        return True
    else:
        print("[!] No changes specified.")
        return False

def main():
    parser = argparse.ArgumentParser(description="Synchronize contact details across website/index.html")
    parser.add_argument("--email", help="New primary email (e.g. contact@bsvr.work)")
    parser.add_argument("--secondary-email", help="New secondary email (e.g. saivardhan@bsvr.work)")
    parser.add_argument("--phone", help="New phone number (e.g. +91 8886244999)")
    parser.add_argument("--github", help="New GitHub username (e.g. SVR1339)")
    parser.add_argument("--twitter", help="New Twitter/X handle (e.g. Svreddy313)")
    parser.add_argument("--instagram", help="New Instagram handle (e.g. svr_313)")

    args = parser.parse_args()

    if not any([args.email, args.secondary_email, args.phone, args.github, args.twitter, args.instagram]):
        print("=== BSVR TECHNOLOGIES CONTACT SYNCHRONIZER (INTERACTIVE MODE) ===")
        print("Press Enter to skip any field you do not wish to change.\n")
        email = input("Primary Email (e.g. contact@bsvr.work): ").strip() or None
        sec_email = input("Secondary Email (e.g. saivardhan@bsvr.work): ").strip() or None
        phone = input("Phone Number (e.g. +91 8886244999): ").strip() or None
        github = input("GitHub Username (e.g. SVR1339): ").strip() or None
        twitter = input("Twitter/X Handle (e.g. Svreddy313): ").strip() or None
        instagram = input("Instagram Handle (e.g. svr_313): ").strip() or None
        update_contact(email, sec_email, phone, github, twitter, instagram)
    else:
        update_contact(args.email, args.secondary_email, args.phone, args.github, args.twitter, args.instagram)

if __name__ == "__main__":
    main()

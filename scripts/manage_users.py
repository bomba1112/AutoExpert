"""Manage accounts on a server without a mail provider (deploy prompt, staging): confirm an e-mail
address, give or take moderator rights (is_admin), list accounts.

    python scripts/manage_users.py list
    python scripts/manage_users.py verify owner@example.com
    python scripts/manage_users.py admin owner@example.com [--off]

On the server: docker compose exec backend python scripts/manage_users.py ...
Passwords are never printed or set here: people register in the app themselves.
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.db.session import SessionLocal  # noqa: E402
from app.models.user import User  # noqa: E402
from sqlalchemy import select  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list")
    verify = sub.add_parser("verify")
    verify.add_argument("email")
    admin = sub.add_parser("admin")
    admin.add_argument("email")
    admin.add_argument("--off", action="store_true")
    args = parser.parse_args()
    with SessionLocal() as db:
        if args.command == "list":
            for user in db.scalars(select(User).where(User.email.not_like("%.invalid")).order_by(User.created_at)):
                print(f"{user.email}\tverified={bool(user.email_verified_at)}\tadmin={user.is_admin}\tactive={user.is_active}")
            return 0
        user = db.scalar(select(User).where(User.email == args.email.casefold()))
        if user is None:
            print("no such account")
            return 1
        if args.command == "verify":
            user.email_verified_at = user.email_verified_at or datetime.now(UTC)
        else:
            user.is_admin = not args.off
        db.commit()
        print(f"{user.email}\tverified={bool(user.email_verified_at)}\tadmin={user.is_admin}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

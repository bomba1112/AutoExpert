"""Generate the staging secrets on the laptop (deploy prompt): the server's .env and the Basic Auth
access for the owner. Written OUTSIDE git, never printed:
    C:/AutoExpertData/secrets/staging.env          -> /srv/autoexpert/shared/.env on the server
    C:/AutoExpertData/secrets/STAGING_ACCESS.txt    -> for the owner (address, user, password)

    uv run --no-project --with bcrypt python deploy/make_secrets.py [--force]

Existing files are kept unless --force (a new password would lock the owner out until it is sent).
"""

from __future__ import annotations

import argparse
import secrets
import sys
from pathlib import Path

import bcrypt

OUT = Path("C:/AutoExpertData/secrets")
TEMPLATE = Path(__file__).with_name(".env.example")
SERVER_IP = "77.42.27.222"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    env_path, access_path = OUT / "staging.env", OUT / "STAGING_ACCESS.txt"
    if (env_path.exists() or access_path.exists()) and not args.force:
        print(f"secrets already exist in {OUT} (kept); --force makes new ones")
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    user = "autoexpert"
    password = secrets.token_urlsafe(18)
    values = {
        "POSTGRES_PASSWORD": secrets.token_urlsafe(32),
        "AUTOEXPERT_SECRET_KEY": secrets.token_urlsafe(48),
        "BASIC_AUTH_USER": user,
        "BASIC_AUTH_HASH": bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode(),
    }
    lines = []
    for line in TEMPLATE.read_text(encoding="utf-8").splitlines():
        if line and not line.startswith("#") and "=" in line:
            name, value = line.split("=", 1)
            value = values.get(name, value)
            # single quotes: compose does not interpolate $ inside (the bcrypt hash has $)
            line = f"{name}='{value}'" if value else f"{name}="
        lines.append(line)
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    access_path.write_text(
        "Auto Expert — закрытый staging (без HTTPS до появления домена)\n"
        f"Адрес: http://{SERVER_IP}/\n"
        f"Пользователь: {user}\n"
        f"Пароль: {password}\n"
        "Не пересылать открытым текстом в мессенджерах; без HTTPS пароль идёт по сети открыто.\n",
        encoding="utf-8")
    print(f"written: {env_path} and {access_path} (values not shown)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

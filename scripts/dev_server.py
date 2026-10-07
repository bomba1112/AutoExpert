"""The local preview on the PostgreSQL staging copy (port 8020), for the Browser pane
(.claude/launch.json "web-preview-pg"). The working SQLite base is not touched.

  .venv/Scripts/python.exe scripts/dev_server.py
"""
import os
import sys
from pathlib import Path

import uvicorn

ROOT = Path(__file__).resolve().parents[1]
os.environ["PATH"] = r"C:\Program Files\PostgreSQL\16\bin" + os.pathsep + os.environ.get("PATH", "")
os.environ.setdefault("PSYCOPG_IMPL", "python")
os.environ.setdefault("AUTOEXPERT_DATABASE_URL", "postgresql+psycopg://autoexpert@localhost:5433/autoexpert_staging")
os.environ.setdefault("AUTOEXPERT_PUBLIC_SITE_DIR", "/nonexistent")
os.environ.setdefault("AUTOEXPERT_CLUB_MEDIA_DIR", "C:/AutoExpertData/staging_media/club")
sys.path.insert(0, str(ROOT / "backend"))

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=int(os.environ.get("PORT", "8020")), access_log=False)

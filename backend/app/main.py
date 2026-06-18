import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.chdir(ROOT)

import db_manager as db
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import accounts, admin, analytics, auth, commentaries, maintenance, prefs, stocks, trades
from app.services import prefs_service

prefs_service.migrate_stored_prefs_file()

db.init_db()

MOUNT = settings.mount_path.rstrip("/")
API_PREFIX = f"{MOUNT}/api"

app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(accounts.router, prefix=API_PREFIX)
app.include_router(trades.router, prefix=API_PREFIX)
app.include_router(admin.router, prefix=API_PREFIX)
app.include_router(analytics.router, prefix=API_PREFIX)
app.include_router(prefs.router, prefix=API_PREFIX)
app.include_router(stocks.router, prefix=API_PREFIX)
app.include_router(commentaries.router, prefix=API_PREFIX)
app.include_router(maintenance.router, prefix=API_PREFIX)


@app.get(f"{API_PREFIX}/health")
def health():
    return {"status": "ok", "version": settings.app_version}


@app.get("/")
def root_redirect():
    return RedirectResponse(url=f"{MOUNT}/", status_code=302)


@app.get("/assets/{asset_path:path}")
def legacy_assets(asset_path: str):
    return RedirectResponse(url=f"{MOUNT}/assets/{asset_path}", status_code=301)


@app.get("/login")
def legacy_login():
    return RedirectResponse(url=f"{MOUNT}/login", status_code=302)


@app.get("/account/{rest:path}")
def legacy_account(rest: str):
    return RedirectResponse(url=f"{MOUNT}/account/{rest}", status_code=302)


@app.get("/client/{rest:path}")
def legacy_client(rest: str):
    return RedirectResponse(url=f"{MOUNT}/client/{rest}", status_code=302)


_palette_root = Path(os.environ.get("PALETTE_STUDIO_ROOT", "")).expanduser()
if _palette_root.is_dir():
    app.mount(
        "/palette",
        StaticFiles(directory=str(_palette_root), html=True),
        name="palette-studio",
    )


_dist = ROOT / "frontend" / "dist"
if _dist.is_dir():
    app.mount(f"{MOUNT}/assets", StaticFiles(directory=_dist / "assets"), name="assets")

    _favicon = _dist / "favicon.svg"
    if _favicon.is_file():

        @app.get(f"{MOUNT}/favicon.svg")
        def favicon():
            return FileResponse(_favicon)

    @app.get(MOUNT, include_in_schema=False)
    def spa_mount_redirect():
        return RedirectResponse(url=f"{MOUNT}/", status_code=301)

    @app.get(f"{MOUNT}/")
    @app.get(f"{MOUNT}/{{full_path:path}}")
    def spa(full_path: str = ""):
        if full_path.startswith("api/") or full_path.startswith("assets/"):
            return {"detail": "Not Found"}
        index = _dist / "index.html"
        return FileResponse(index)

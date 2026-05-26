"""
Persistence layer — três modos (detectados automaticamente):

  1. GitHub Gist  → GITHUB_TOKEN + GIST_ID em st.secrets   (recomendado cloud)
  2. Supabase     → SUPABASE_URL + SUPABASE_KEY em st.secrets
  3. JSON local   → data/app_data.json                      (dev / fallback)

Todos os modos tentam salvar localmente como backup.
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional

_LOCAL_FILE = Path(__file__).parent.parent / "data" / "app_data.json"
_GIST_FILENAME = "beach_friends_data.json"


# ─────────────────────────────────────────────
#  Secrets helper
# ─────────────────────────────────────────────

def _secret(key: str, default: str = "") -> str:
    try:
        import streamlit as st
        return st.secrets.get(key, default)
    except Exception:
        return os.environ.get(key, default)


# ─────────────────────────────────────────────
#  GitHub Gist
# ─────────────────────────────────────────────

def _gist_headers() -> dict:
    token = _secret("GITHUB_TOKEN")
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }


def _gist_load() -> Optional[Dict]:
    gist_id = _secret("GIST_ID")
    if not gist_id or not _secret("GITHUB_TOKEN"):
        return None
    try:
        import requests
        r = requests.get(
            f"https://api.github.com/gists/{gist_id}",
            headers=_gist_headers(), timeout=8,
        )
        if r.status_code == 200:
            content = r.json()["files"].get(_GIST_FILENAME, {}).get("content", "")
            if content:
                return json.loads(content)
    except Exception:
        pass
    return None


def _gist_save(data: Dict) -> None:
    gist_id = _secret("GIST_ID")
    if not gist_id or not _secret("GITHUB_TOKEN"):
        return
    try:
        import requests
        requests.patch(
            f"https://api.github.com/gists/{gist_id}",
            headers=_gist_headers(),
            json={"files": {_GIST_FILENAME: {"content": json.dumps(data, ensure_ascii=False)}}},
            timeout=8,
        )
    except Exception:
        pass


# ─────────────────────────────────────────────
#  Supabase  (mantido como alternativa)
# ─────────────────────────────────────────────

def _sb_load() -> Optional[Dict]:
    url, key = _secret("SUPABASE_URL"), _secret("SUPABASE_KEY")
    if not url or not key:
        return None
    try:
        from supabase import create_client
        res = create_client(url, key).table("arena_bt").select("data").eq("id", 1).execute()
        if res.data:
            return res.data[0]["data"]
    except Exception:
        pass
    return None


def _sb_save(data: Dict) -> None:
    url, key = _secret("SUPABASE_URL"), _secret("SUPABASE_KEY")
    if not url or not key:
        return
    try:
        from supabase import create_client
        create_client(url, key).table("arena_bt").upsert({"id": 1, "data": data}).execute()
    except Exception:
        pass


# ─────────────────────────────────────────────
#  JSON local
# ─────────────────────────────────────────────

def _local_load() -> Optional[Dict]:
    if _LOCAL_FILE.exists():
        try:
            return json.loads(_LOCAL_FILE.read_text("utf-8"))
        except Exception:
            pass
    return None


def _local_save(data: Dict) -> None:
    _LOCAL_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = _LOCAL_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
    try:
        tmp.replace(_LOCAL_FILE)
    except Exception:
        os.replace(str(tmp), str(_LOCAL_FILE))


# ─────────────────────────────────────────────
#  Public API
# ─────────────────────────────────────────────

def default_data() -> Dict:
    from .auth import default_admin_hash
    return {
        "admin_password_hash": default_admin_hash(),
        "players": {},
        "tournament": None,
    }


def load() -> Dict:
    # Priority: Gist → Supabase → Local
    for fn in (_gist_load, _sb_load, _local_load):
        data = fn()
        if data is not None:
            return data
    return default_data()


def save(data: Dict) -> None:
    # Save to whichever cloud is configured + always local backup
    _gist_save(data)
    _sb_save(data)
    _local_save(data)

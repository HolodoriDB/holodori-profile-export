from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path

from .. import profile, text
from ..client import GameClient

_REL = Path("AppData/LocalLow/QualiArts, Inc_/hololive-Dreams")


def game_data_dir() -> Path:
    base = os.environ.get("USERPROFILE") or str(Path.home())
    return Path(base) / _REL


def read_credential() -> str:
    root = game_data_dir()
    if not root.is_dir():
        raise FileNotFoundError(text.ERR_STEAM_NO_FOLDER.format(root=root))
    dc = sorted(
        (p for p in root.iterdir() if p.is_file() and p.name.startswith("DC")),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not dc:
        raise FileNotFoundError(text.ERR_STEAM_NO_FILE.format(root=root))
    cred = dc[0].read_text("utf-8-sig").replace("﻿", "").strip()
    if not cred:
        raise ValueError(text.ERR_STEAM_EMPTY.format(name=dc[0].name))
    return cred


def run(
    client: GameClient, out_dir: str, echo: Callable[[str], None] = print
) -> tuple[dict, Path]:
    cred = read_credential()
    echo(text.STATUS_STEAM_LOGIN)
    ud = client.user_get(client.auth_login(cred))
    obj = profile.build(ud)
    dest = profile.write(obj, out_dir)
    return obj, dest

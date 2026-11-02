from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from .. import profile, text
from ..client import GameClient


def run(
    client: GameClient,
    credential: str,
    out_dir: str,
    echo: Callable[[str], None] = print,
) -> tuple[dict, Path]:
    echo(text.STATUS_CREDENTIAL_LOGIN)
    ud = client.user_get(client.auth_login(credential))
    obj = profile.build(ud)
    dest = profile.write(obj, out_dir)
    return obj, dest

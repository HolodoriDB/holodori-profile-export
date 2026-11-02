from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from .. import profile, text
from ..client import GameClient


def run(
    client: GameClient,
    migration_id: str,
    password: str,
    out_dir: str,
    echo: Callable[[str], None] = print,
) -> tuple[dict, Path]:
    echo(text.STATUS_TRANSFER_VALIDATE)
    info = client.migration_prepare_password(migration_id, password)
    if not info.get("public_user_id") or not info.get("one_time_token"):
        raise RuntimeError(text.ERR_TRANSFER_REJECTED)
    echo(
        text.STATUS_TRANSFER_ACCOUNT.format(
            name=info.get("user_name") or "?", level=info.get("player_level")
        )
    )

    echo(text.STATUS_TRANSFER_LOAD)
    credential, _ = client.migration_migrate(
        info["public_user_id"], info["one_time_token"]
    )
    ud = client.user_get(client.auth_login(credential))
    obj = profile.build(ud)
    dest = profile.write(obj, out_dir)
    return obj, dest

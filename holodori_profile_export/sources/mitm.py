"""mitmproxy addon: observe the game client's traffic and write the .hdbest from the account
snapshot it sees. non-destructive. see the README for how to run it."""

from __future__ import annotations

import os

from holodori_asset_tools import api

from .. import profile, proto, schema, text
from ..client import require_asset_tools

_HOST = "game-hololive-dreams.com"


class HdbestCapture:
    def __init__(self) -> None:
        require_asset_tools()
        self.done = False

    def load(self, loader) -> None:  # mitmproxy hook
        loader.add_option("hdbest_out", str, os.getcwd(), text.MITM_OUT_OPTION)

    def _userdata_from(self, path: str, body: bytes) -> dict[int, list] | None:
        resp = proto.decode(api.decode_response(body))
        if path.endswith("User/Get"):
            ud = proto.get(resp, schema.field("UserGetResponse", "user_data"))
        elif path.endswith("Home/Login"):
            common = proto.get(
                resp, schema.field("HomeLoginResponse", "common_response")
            )
            cm = proto.decode(common) if isinstance(common, (bytes, bytearray)) else {}
            ud = proto.get(cm, schema.field("Response", "updated_data"))
        else:
            return None
        return proto.decode(ud) if isinstance(ud, (bytes, bytearray)) else None

    def response(self, flow) -> None:  # mitmproxy hook
        if self.done or _HOST not in flow.request.host:
            return
        ct = flow.response.headers.get("content-type", "")
        if not ct.startswith("application/grpc+proto-enc"):
            return
        if not (
            flow.request.path.endswith("User/Get")
            or flow.request.path.endswith("Home/Login")
        ):
            return
        try:
            ud = self._userdata_from(
                flow.request.path, flow.response.raw_content or b""
            )
            if not ud:
                return
            obj = profile.build(ud)
            counts = profile.summary(obj)
            if not counts["cards"] and not counts["songs"]:
                return  # pre-login/empty snapshot; keep waiting
            dest = profile.write(obj, ctx_out())
            self.done = True
            print(
                text.MITM_CAPTURED.format(
                    cards=counts["cards"], songs=counts["songs"], dest=dest
                )
            )
        except Exception as e:
            print(text.MITM_DECODE_FAILED.format(path=flow.request.path, error=e))


def ctx_out() -> str:
    try:
        from mitmproxy import ctx

        return ctx.options.hdbest_out or os.getcwd()
    except Exception:
        return os.getcwd()


addons = [HdbestCapture()]

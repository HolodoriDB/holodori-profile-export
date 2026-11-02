"""mitmproxy addon: observe the game client's traffic and write the .hdbest from the account
snapshot it sees. non-destructive. see the README for how to run it."""

from __future__ import annotations

import os

from holodori_asset_tools import api

from .. import profile, proto, text

_HOST = "game-hololive-dreams.com"


class HdbestCapture:
    def __init__(self) -> None:
        self.done = False

    def load(self, loader) -> None:  # mitmproxy hook
        loader.add_option("hdbest_out", str, os.getcwd(), text.MITM_OUT_OPTION)

    def _region(self, host: str) -> str:
        sub = host.split(".", 1)[0]
        return sub if sub in ("as", "us", "jp") else "us"

    def _userdata_from(self, path: str, body: bytes):
        resp = proto.decode(api.decode_response(body))
        if path.endswith("User/Get"):
            ud = proto.get(resp, 1)  # UserGetResponse{1: UserData}
            return proto.decode(ud) if isinstance(ud, (bytes, bytearray)) else None
        if path.endswith("Home/Login"):
            common = proto.get(resp, 9999)  # common.Response{1: updated_data=UserData}
            cm = proto.decode(common) if isinstance(common, (bytes, bytearray)) else {}
            ud = proto.get(cm, 1)
            return proto.decode(ud) if isinstance(ud, (bytes, bytearray)) else None
        return None

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
            obj = profile.build(ud, self._region(flow.request.host))
            if not obj["cards"] and not obj["songs"]:
                return  # pre-login/empty snapshot; keep waiting
            dest = profile.write(obj, ctx_out())
            self.done = True
            print(
                text.MITM_CAPTURED.format(
                    cards=len(obj["cards"]), songs=len(obj["songs"]), dest=dest
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

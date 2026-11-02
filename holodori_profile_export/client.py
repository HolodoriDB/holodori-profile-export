from __future__ import annotations

from curl_cffi import requests

from holodori_asset_tools import api, catalog

from . import proto, schema, text

AUTH_LOGIN = "rpc.api.Auth/Login"
MIG_PREP_PASSWORD = "rpc.api.AccountMigration/PrepareMigrationPassword"
MIG_MIGRATE = "rpc.api.AccountMigration/Migrate"
MASTER_GET = "rpc.api.Master/Get"
USER_GET = "rpc.api.User/Get"

_REGION_LANG = {"as": "eng", "us": "eng", "jp": "jpn"}

_BASE_HEADERS = {
    "content-type": "application/grpc+proto-enc",
    "te": "trailers",
    "user-agent": "grpc-dotnet/2.76.0 (Mono Unity; CLR 4.0.30319.17020; netstandard2.1; arm64)",
    "grpc-accept-encoding": "identity,gzip",
    "grpc-timeout": "30S",
    "x-app-store-type": "GooglePlay",
    "x-app-device-name": "SONY SO-41B",
    "x-app-os-version": "Android OS 14 / API-34 (UQ1A.240205.07131809/ucsm.20260713.180933)",
    "x-app-os-type": "Android",
    "x-app-bundle-id": "game.qualiarts.hololive.dreams.com",
    "x-app-cpu": "x86-64 SSE3 SSE4.1 SSE4.2 AVX",
    "x-app-gpu": "Adreno (TM) 750",
    "x-app-operating-system-family": "Other",
    "x-app-device-type": "Handheld",
    "x-app-graphics-device-type": "Vulkan",
    "x-app-graphics-device-version": "Vulkan 1.1.0 [2.0.395 (0x0080018b)]",
    "x-app-graphics-device-vendor-id": "20803",
    "x-app-graphics-device-memory-size": "1536",
    "x-app-graphics-shader-level": "50",
    "x-app-processor-model": "x86-64 SSE3 SSE4.1 SSE4.2 AVX",
    "x-app-processor-count": "4",
    "x-app-system-memory-size": "3934",
    "x-app-screen-dpi": "280",
    "x-app-screen-height": "1080",
    "x-app-screen-width": "1920",
    "x-a-ise": "False",
    "x-a-isda": "False",
    "x-a-isop": "False",
    "x-a-isr": "False",
}


class GameError(RuntimeError):
    pass


class GameClient:
    def __init__(self, region: str = "us") -> None:
        if region not in _REGION_LANG:
            raise ValueError(f"region must be one of {sorted(_REGION_LANG)}")
        self.region = region
        self.base_url = f"https://{region}.game-hololive-dreams.com"
        self.lang = _REGION_LANG[region]
        self.session = requests.Session(impersonate="chrome", timeout=30)
        self.master_version: str | None = None

    def close(self) -> None:
        try:
            self.session.close()
        except Exception:
            pass

    def __enter__(self) -> "GameClient":
        return self

    def __exit__(self, *_) -> None:
        self.close()

    def _headers(self, token: str | None) -> dict[str, str]:
        h = dict(_BASE_HEADERS)
        h["x-app-version"] = catalog.appver().get("version_name") or "1.0.0"
        h["x-app-lang-type"] = self.lang
        h["x-app-request-id"] = api.app_request_id()
        if self.master_version:
            h["x-app-master-version"] = self.master_version
        if token:
            h["x-app-auth-token"] = token
        return h

    def call(
        self, method: str, body: bytes = b"", token: str | None = None
    ) -> dict[int, list]:
        data = api.frame(api.encrypt(body) if body else b"")
        r = self.session.post(
            f"{self.base_url}/{method}", headers=self._headers(token), data=data
        )
        gs = r.headers.get("grpc-status")
        ct = r.headers.get("content-type", "")
        if ct.startswith("application/grpc+proto-enc") and gs in (None, "0"):
            if len(r.content) < 5:
                return {}
            return proto.decode(api.decode_response(r.content))
        if r.headers.get("x-app-error-code") == "2004":
            raise GameError(
                text.ERR_APP_OUTDATED.format(
                    method=method, version=self._headers(None)["x-app-version"]
                )
            )
        if ct.startswith("application/grpc") and gs == "16":
            raise GameError(text.ERR_UNAUTHENTICATED.format(method=method))
        raise GameError(
            text.ERR_CALL_FAILED.format(
                method=method, status=r.status_code, gs=gs, ct=ct, size=len(r.content)
            )
        )

    def auth_login(self, credential: str) -> str:
        return proto.get_str(
            self.call(AUTH_LOGIN, proto.string_field(1, credential)), 1
        )

    def _linked_user_info(self, resp: dict[int, list]) -> dict:
        lr = proto.get(resp, 1)
        link = proto.decode(lr) if isinstance(lr, (bytes, bytearray)) else {}
        info_raw = proto.get(link, 2)
        info = (
            proto.decode(info_raw) if isinstance(info_raw, (bytes, bytearray)) else {}
        )
        return {
            "is_already_linked": bool(proto.get_int(link, 1)),
            "public_user_id": proto.get_str(info, 1),
            "user_name": proto.get_str(info, 2),
            "player_level": proto.get_int(info, 3),
            "one_time_token": proto.get_str(info, 4),
            "region": proto.get_int(info, 5),
        }

    def migration_prepare_password(
        self, account_migration_id: str, password: str
    ) -> dict:
        resp = self.call(
            MIG_PREP_PASSWORD,
            proto.message(
                proto.string_field(1, account_migration_id),
                proto.string_field(2, password),
            ),
        )
        return self._linked_user_info(resp)

    def migration_migrate(
        self,
        target_public_user_id: str,
        one_time_token: str,
        previous_public_user_id: str = "",
    ) -> tuple[str, str]:
        parts = [
            proto.string_field(2, target_public_user_id),
            proto.string_field(3, one_time_token),
        ]
        if previous_public_user_id:
            parts.insert(0, proto.string_field(1, previous_public_user_id))
        d = self.call(MIG_MIGRATE, proto.message(*parts))
        return proto.get_str(d, 1), proto.get_str(d, 2)

    def ensure_master_version(self) -> None:
        # data RPCs (User/Get, Home/Login) are gated on x-app-master-version; Master/Get itself is
        # exempt, so fetch the current version from it once (no auth, empty request) and reuse it.
        if self.master_version is None:
            resp = self.call(MASTER_GET)
            self.master_version = proto.get_str(
                resp, schema.field("MasterGetResponse", "version")
            )

    def user_get(self, token: str) -> dict[int, list]:
        self.ensure_master_version()
        resp = self.call(USER_GET, token=token)
        ud = proto.get(resp, schema.field("UserGetResponse", "user_data"))
        return proto.decode(ud) if isinstance(ud, (bytes, bytearray)) else {}

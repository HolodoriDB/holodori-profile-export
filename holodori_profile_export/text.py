from __future__ import annotations

APP_HELP = "Export your hololive Dreams account to a .hdbest profile for holodori.best"
OPT_SOURCE = "Account source"
OPT_REGION = "Account region (us, as, jp)."
OPT_OUT = "Output folder for the .hdbest."
OPT_MIGRATION_ID = "In-game transfer id (link ID)."
OPT_PASSWORD = "In-game transfer password."
OPT_CREDENTIAL = "The raw account credential."
OPT_YES = "Skip confirmations."
OPT_JSON = "Output JSON."
OPT_QUIET = "Errors only."
OPT_VERSION = "Show version."

ASK_REGION = "Region"
ASK_TRANSFER_ID = "Transfer id (link ID)"
ASK_TRANSFER_PASSWORD = "Transfer password"
ASK_CREDENTIAL = "Credential"
CONFIRM_TRANSFER = (
    "This logs the game out on your device (you can log back in). Continue?"
)

STATUS_STEAM_LOGIN = "Logging in with the cached credential ..."
STATUS_TRANSFER_VALIDATE = "Checking the transfer id and password ..."
STATUS_TRANSFER_ACCOUNT = "Account: {name} (lv {level})"
STATUS_TRANSFER_LOAD = "Downloading account data ..."
STATUS_CREDENTIAL_LOGIN = "Logging in ..."

RESULT_TITLE = "Exported"
ROW_ACCOUNT = "Account"
ROW_PUBLIC_ID = "Public ID"
ROW_REGION = "Region"
ROW_CARDS = "Cards"
ROW_SONGS = "Songs"
ROW_HOLOMEMS = "Holomems"
RESULT_DONE = "saved {dest}"
TRANSFER_NOTE = "Log back in by restarting the game on your real device."
UPLOAD_HINT = "Upload the .hdbest on holodori.best."

ERR_PREFIX = "error:"
ERR_UNEXPECTED = "unexpected error:"
ERR_ABORTED = "aborted"
ERR_NEED = "missing {flag}."
ERR_TRANSFER_REJECTED = "transfer id or password is wrong."
ERR_BAD_LINK_ID = "transfer id must be 8 characters."
ERR_BAD_PASSWORD = "transfer password must be 8-16 characters."
ERR_SCHEMA_DOWNLOAD = "couldn't download the proto schema: {error}"
ERR_SCHEMA_FIELD = (
    "the game's proto schema has no {message}.{field}; this tool is out of date."
)
ERR_STEAM_NO_FOLDER = "game data folder not found at {root}. Launch hololive Dreams on this PC and log in first."
ERR_STEAM_NO_FILE = (
    "no account credential (DC*) file in {root}. Launch the game and log in first."
)
ERR_STEAM_EMPTY = "credential file {name} is empty."
ERR_APP_OUTDATED = (
    "the game updated and this tool is out of date. Waiting a few hours is usually enough for it "
    "to update automatically."
)
ERR_UNAUTHENTICATED = "login rejected."
ERR_CALL_FAILED = "{method} failed (http={status} grpc-status={gs})."

MITM_INSTRUCTIONS = (
    "Run the mitmproxy addon and route the game client through it:\n"
    "    pip install mitmproxy\n"
    "    mitmdump -s holodori_profile_export/sources/mitm.py --set hdbest_out=.\n"
    "Then launch/relaunch the game (proxied, mitm CA trusted). The addon writes the .hdbest when "
    "it sees the home-screen snapshot."
)
MITM_CAPTURED = "[mitm] captured {cards} cards, {songs} songs -> {dest}"
MITM_DECODE_FAILED = "[mitm] decode failed on {path}: {error}"
MITM_OUT_OPTION = "directory to write the .hdbest into"

GUI_TITLE = "holodori profile export"
GUI_BTN_NEXT = "Next"
GUI_BTN_BACK = "Back"
GUI_BTN_START = "Start"
GUI_BTN_CLOSE = "Close"
GUI_BTN_BROWSE = "Browse"
GUI_LABEL_WHEREFROM = "Where from"
GUI_LABEL_REGION = "Region"
GUI_LABEL_SAVETO = "Save to"
GUI_SRC_STEAM = "Steam (PC)"
GUI_SRC_TRANSFER = "Transfer code"
GUI_SRC_CREDENTIAL = "Credential"

GUI_STEP1_TITLE = "Import your game data"
GUI_STEP1_SUB = "Export your account to a .hdbest profile for holodori.best."
GUI_HINT_STEAM = (
    "Loads your game account from the Steam version of the game (Windows only). You must have "
    "logged in on the Steam version of the game for this to work."
)
GUI_HINT_TRANSFER = (
    "Log in with your account transfer id (link id) and password. This will temporarily log the "
    "game out on your device; you can log back in by restarting the game."
)
GUI_HINT_CREDENTIAL = "Advanced: log in with a raw account credential you already have."

GUI_STEAM_TITLE = "Steam import"
GUI_STEAM_SUB = "Downloads into {out}"
GUI_CRED_TITLE = "Credential"
GUI_CRED_SUB = "Advanced. Paste a raw account credential you already have."
GUI_CRED_FIELD = "Credential"
GUI_TRANSFER_TITLE = "Transfer code"
GUI_TRANSFER_SUB = "Enter the data-transfer credentials from the game."
GUI_TRANSFER_WARN = "This temporarily logs the game out on your device; log back in by restarting the game."
GUI_TRANSFER_FIELD_ID = "Transfer id (link id)"
GUI_TRANSFER_FIELD_PW = "Transfer password"

GUI_WORKING_TITLE = "Working ..."
GUI_WORKING_SUB = "Talking to the game servers ..."
GUI_DONE_TITLE = "Done"
GUI_DONE_SUB = "Saved to {dest}"
GUI_DONE_TRANSFER_NOTE = "Log back in by restarting the game on your device."
GUI_DONE_UPLOAD = "Upload the .hdbest on holodori.best."
GUI_ERROR_TITLE = "Something went wrong"

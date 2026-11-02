from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Annotated, Any, NoReturn, Optional

import typer
from rich import box
from rich.console import Console
from rich.markup import escape
from rich.prompt import Confirm, Prompt
from rich.table import Table

from . import __version__, text
from .client import GameClient, GameError
from .sources import credential as credential_source
from .sources import steam as steam_source
from .sources import transfer as transfer_source


class Code(IntEnum):
    OK = 0
    UNEXPECTED = 1
    USAGE = 2
    FAILED = 4
    ABORTED = 130


class Source(str, Enum):
    steam = "steam"
    transfer = "transfer"
    credential = "credential"
    mitm = "mitm"


class CliError(Exception):
    def __init__(self, message: str, code: Code) -> None:
        super().__init__(message)
        self.code = code


def fail(message: str, code: Code) -> NoReturn:
    raise CliError(message, code)


def _is_link_id(v: str) -> bool:
    return len(v) == 8


def _is_password(v: str) -> bool:
    return 8 <= len(v) <= 16


def require(value: str, ok: Callable[[str], bool], error: str) -> None:
    if not ok(value):
        fail(error, Code.USAGE)


@dataclass
class Ui:
    json: bool = False
    quiet: bool = False
    yes: bool = False
    out: Console = field(init=False)
    err: Console = field(init=False)

    def __post_init__(self) -> None:
        self.out = Console(stderr=self.json, quiet=self.quiet, highlight=False)
        self.err = Console(stderr=True, highlight=False)

    @property
    def interactive(self) -> bool:
        return not (self.yes or self.quiet)

    def print(self, *objects: Any) -> None:
        self.out.print(*objects)

    def status(self, message: str) -> None:
        if not self.quiet:
            self.err.print(f"[dim]{escape(message)}[/]")

    def emit(self, data: dict[str, Any]) -> None:
        if self.json:
            print(json.dumps(data, ensure_ascii=False, indent=2))

    def ask(
        self,
        question: str,
        flag: str,
        *,
        password: bool = False,
        ok: Callable[[str], bool] | None = None,
        error: str = "",
    ) -> str:
        if not self.interactive:
            fail(text.ERR_NEED.format(flag=flag), Code.USAGE)
        while True:
            try:
                answer = Prompt.ask(
                    question, console=self.err, password=password
                ).strip()
            except EOFError:
                fail(text.ERR_NEED.format(flag=flag), Code.USAGE)
            if ok is None or ok(answer):
                return answer
            self.err.print(f"[red]{escape(error)}[/]")

    def choose(self, question: str, choices: list[str], flag: str) -> str:
        if not self.interactive:
            fail(text.ERR_NEED.format(flag=flag), Code.USAGE)
        try:
            return Prompt.ask(question, console=self.err, choices=choices)
        except EOFError:
            fail(text.ERR_NEED.format(flag=flag), Code.USAGE)

    def confirm(self, question: str, default: bool) -> bool:
        if not self.interactive:
            return True
        try:
            return Confirm.ask(question, console=self.err, default=default)
        except EOFError:
            return default


def result_table(obj: dict) -> Table:
    table = Table(
        title=text.RESULT_TITLE,
        box=box.ROUNDED,
        show_header=False,
        title_justify="left",
    )
    table.add_column(style="bold cyan")
    table.add_column()
    table.add_row(text.ROW_ACCOUNT, escape(obj.get("userName") or "?"))
    table.add_row(text.ROW_PUBLIC_ID, escape(obj.get("publicUserId") or "?"))
    table.add_row(text.ROW_REGION, escape(str(obj.get("region"))))
    table.add_row(text.ROW_CARDS, str(len(obj.get("cards", []))))
    table.add_row(text.ROW_SONGS, str(len(obj.get("songs", []))))
    table.add_row(text.ROW_HOLOMEMS, str(len(obj.get("holomems", []))))
    return table


def show_result(ui: Ui, obj: dict, dest: str, source: str) -> None:
    ui.print(result_table(obj))
    ui.print(f"[green]done[/] {escape(text.RESULT_DONE.format(dest=dest))}")
    if source == "transfer":
        ui.status(text.TRANSFER_NOTE)
    ui.status(text.UPLOAD_HINT)
    ui.emit(
        {
            "dest": str(dest),
            "source": source,
            "region": obj.get("region"),
            "publicUserId": obj.get("publicUserId"),
            "userName": obj.get("userName"),
            "cards": len(obj.get("cards", [])),
            "songs": len(obj.get("songs", [])),
            "holomems": len(obj.get("holomems", [])),
        }
    )


def _report(ui: Ui, message: str, code: Code) -> NoReturn:
    if ui.json:
        print(
            json.dumps({"error": message, "exit_code": int(code)}, ensure_ascii=False)
        )
    else:
        ui.err.print(f"[red]{text.ERR_PREFIX}[/] {escape(message)}")
    raise typer.Exit(int(code))


def handle(ui: Ui, body) -> None:
    try:
        body()
    except CliError as e:
        _report(ui, str(e), e.code)
    except typer.Exit:
        raise
    except (KeyboardInterrupt, typer.Abort):
        ui.err.print(f"[yellow]{escape(text.ERR_ABORTED)}[/]")
        raise typer.Exit(int(Code.ABORTED))
    except (GameError, OSError, ValueError, RuntimeError) as e:
        _report(ui, str(e), Code.FAILED)
    except Exception as e:  # noqa: BLE001 - last-resort reporting
        ui.err.print(
            f"[red]{text.ERR_UNEXPECTED}[/] {escape(f'{type(e).__name__}: {e}')}"
        )
        raise typer.Exit(int(Code.UNEXPECTED))


def version_callback(value: bool) -> None:
    if value:
        print(f"holodori-profile-export {__version__}")
        raise typer.Exit()


app = typer.Typer(
    name="holodori-profile-export",
    help=text.APP_HELP,
    add_completion=False,
    pretty_exceptions_enable=False,
    rich_markup_mode="rich",
)


@app.callback(invoke_without_command=True)
def main(
    source: Annotated[Source, typer.Option("--source", "-s", help=text.OPT_SOURCE)],
    region: Annotated[
        Optional[str], typer.Option("--region", "-r", help=text.OPT_REGION)
    ] = None,
    out: Annotated[str, typer.Option("--out", "-o", help=text.OPT_OUT)] = ".",
    migration_id: Annotated[
        Optional[str], typer.Option("--migration-id", help=text.OPT_MIGRATION_ID)
    ] = None,
    password: Annotated[
        Optional[str], typer.Option("--password", help=text.OPT_PASSWORD)
    ] = None,
    credential: Annotated[
        Optional[str], typer.Option("--credential", help=text.OPT_CREDENTIAL)
    ] = None,
    yes: Annotated[bool, typer.Option("--yes", "-y", help=text.OPT_YES)] = False,
    json_: Annotated[bool, typer.Option("--json", help=text.OPT_JSON)] = False,
    quiet: Annotated[bool, typer.Option("--quiet", "-q", help=text.OPT_QUIET)] = False,
    version: Annotated[
        bool,
        typer.Option(
            "--version", callback=version_callback, is_eager=True, help=text.OPT_VERSION
        ),
    ] = False,
) -> None:
    ui = Ui(json=json_, quiet=quiet, yes=yes)

    def body() -> None:
        if source is Source.mitm:
            ui.print(text.MITM_INSTRUCTIONS)
            return

        reg = region or ui.choose(text.ASK_REGION, ["us", "as", "jp"], "--region")
        with GameClient(reg) as client:
            if source is Source.steam:
                obj, dest = steam_source.run(client, out, echo=ui.status)
            elif source is Source.credential:
                cred = credential or ui.ask(
                    text.ASK_CREDENTIAL, "--credential", password=True
                )
                obj, dest = credential_source.run(client, cred, out, echo=ui.status)
            else:
                if migration_id is None:
                    mig = ui.ask(
                        text.ASK_TRANSFER_ID,
                        "--migration-id",
                        ok=_is_link_id,
                        error=text.ERR_BAD_LINK_ID,
                    )
                else:
                    require(migration_id, _is_link_id, text.ERR_BAD_LINK_ID)
                    mig = migration_id
                if password is None:
                    pwd = ui.ask(
                        text.ASK_TRANSFER_PASSWORD,
                        "--password",
                        password=True,
                        ok=_is_password,
                        error=text.ERR_BAD_PASSWORD,
                    )
                else:
                    require(password, _is_password, text.ERR_BAD_PASSWORD)
                    pwd = password
                if not ui.confirm(text.CONFIRM_TRANSFER, True):
                    fail(text.ERR_ABORTED, Code.ABORTED)
                obj, dest = transfer_source.run(client, mig, pwd, out, echo=ui.status)

        show_result(ui, obj, str(dest), source.value)

    handle(ui, body)


def run(argv: list[str]) -> int:
    try:
        app(args=argv, prog_name="holodori-profile-export")
    except SystemExit as e:
        return e.code if isinstance(e.code, int) else int(e.code is not None)
    return 0

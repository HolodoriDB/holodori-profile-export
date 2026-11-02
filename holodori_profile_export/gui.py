from __future__ import annotations

import os
import queue
import sys
import threading
from importlib.resources import files

import customtkinter as ctk
from tkinter import PhotoImage, filedialog

from . import text
from .client import GameClient
from .sources import credential, steam, transfer

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

_SOURCES = {
    text.GUI_SRC_STEAM: "steam",
    text.GUI_SRC_TRANSFER: "transfer",
    text.GUI_SRC_CREDENTIAL: "credential",
}
_LABEL_FOR = {v: k for k, v in _SOURCES.items()}
_HINTS = {
    "steam": text.GUI_HINT_STEAM,
    "transfer": text.GUI_HINT_TRANSFER,
    "credential": text.GUI_HINT_CREDENTIAL,
}


class App(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title(text.GUI_TITLE)
        self.geometry("560x520")
        self.minsize(500, 460)
        self._set_icon()
        self.after(250, self._set_icon)
        self.q: queue.Queue = queue.Queue()
        self.source = "steam"
        self.region = "us"
        self.out_dir = os.getcwd()

        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=28, pady=24)
        self._step_source()

    def _set_icon(self) -> None:
        try:
            assets = files("holodori_profile_export") / "assets"
            if sys.platform == "win32":
                self.iconbitmap(str(assets / "favicon.ico"))
            else:
                self._icon = PhotoImage(file=str(assets / "icon.png"))
                self.iconphoto(True, self._icon)
        except Exception:
            pass

    def _clear(self) -> None:
        for w in self.body.winfo_children():
            w.destroy()

    def _title(self, title: str, sub: str | None = None) -> None:
        ctk.CTkLabel(
            self.body, text=title, font=ctk.CTkFont(size=24, weight="bold")
        ).pack(anchor="w")
        if sub:
            ctk.CTkLabel(
                self.body,
                text=sub,
                text_color=("gray45", "gray62"),
                wraplength=480,
                justify="left",
            ).pack(anchor="w", pady=(4, 18))

    def _nav(self, *, back=None, next_text=text.GUI_BTN_NEXT, next_cmd=None):
        row = ctk.CTkFrame(self.body, fg_color="transparent")
        row.pack(side="bottom", fill="x", pady=(18, 0))
        if back:
            ctk.CTkButton(
                row,
                text=text.GUI_BTN_BACK,
                width=90,
                fg_color="transparent",
                border_width=1,
                command=back,
            ).pack(side="left")
        ctk.CTkButton(row, text=next_text, width=140, command=next_cmd).pack(
            side="right"
        )

    def _step_source(self) -> None:
        self._clear()
        self._title(text.GUI_STEP1_TITLE, text.GUI_STEP1_SUB)

        ctk.CTkLabel(self.body, text=text.GUI_LABEL_WHEREFROM, anchor="w").pack(
            fill="x"
        )
        seg = ctk.CTkSegmentedButton(
            self.body, values=list(_SOURCES), command=self._pick_source
        )
        seg.set(_LABEL_FOR[self.source])
        seg.pack(fill="x", pady=(4, 6))
        self._source_hint = ctk.CTkLabel(
            self.body,
            text="",
            text_color=("gray45", "gray62"),
            wraplength=480,
            justify="left",
        )
        self._source_hint.pack(anchor="w")
        self._pick_source(seg.get())

        ctk.CTkLabel(self.body, text=text.GUI_LABEL_REGION, anchor="w").pack(
            fill="x", pady=(16, 0)
        )
        self._region_menu = ctk.CTkOptionMenu(self.body, values=["us", "as", "jp"])
        self._region_menu.set(self.region)
        self._region_menu.pack(anchor="w", pady=(4, 0))

        ctk.CTkLabel(self.body, text=text.GUI_LABEL_SAVETO, anchor="w").pack(
            fill="x", pady=(16, 0)
        )
        row = ctk.CTkFrame(self.body, fg_color="transparent")
        row.pack(fill="x", pady=(4, 0))
        self._out_entry = ctk.CTkEntry(row)
        self._out_entry.insert(0, self.out_dir)
        self._out_entry.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(
            row, text=text.GUI_BTN_BROWSE, width=80, command=self._browse
        ).pack(side="left", padx=(8, 0))

        self._nav(next_cmd=self._from_source)

    def _pick_source(self, label: str) -> None:
        self.source = _SOURCES[label]
        self._source_hint.configure(text=_HINTS[self.source])

    def _browse(self) -> None:
        d = filedialog.askdirectory(initialdir=self._out_entry.get() or os.getcwd())
        if d:
            self._out_entry.delete(0, "end")
            self._out_entry.insert(0, d)

    def _from_source(self) -> None:
        self.region = self._region_menu.get()
        self.out_dir = self._out_entry.get().strip() or os.getcwd()
        self._step_details()

    def _step_details(self) -> None:
        self._clear()
        if self.source == "steam":
            self._title(
                text.GUI_STEAM_TITLE, text.GUI_STEAM_SUB.format(out=self.out_dir)
            )
            self._nav(
                back=self._step_source, next_text=text.GUI_BTN_START, next_cmd=self._run
            )
            return

        if self.source == "credential":
            self._title(text.GUI_CRED_TITLE, text.GUI_CRED_SUB)
            self._cred = self._field(text.GUI_CRED_FIELD)
            self._nav(
                back=self._step_source, next_text=text.GUI_BTN_START, next_cmd=self._run
            )
            return

        self._title(text.GUI_TRANSFER_TITLE, text.GUI_TRANSFER_SUB)
        ctk.CTkLabel(
            self.body,
            text=text.GUI_TRANSFER_WARN,
            text_color=("gray45", "gray62"),
            wraplength=480,
            justify="left",
        ).pack(anchor="w", pady=(0, 14))
        self._mig = self._field(text.GUI_TRANSFER_FIELD_ID)
        self._pwd = self._field(text.GUI_TRANSFER_FIELD_PW, show="•")
        self._nav(
            back=self._step_source, next_text=text.GUI_BTN_START, next_cmd=self._run
        )

    def _field(self, label: str, show: str = "") -> ctk.CTkEntry:
        ctk.CTkLabel(self.body, text=label, anchor="w").pack(fill="x", pady=(8, 0))
        e = ctk.CTkEntry(self.body, show=show)
        e.pack(fill="x", pady=(4, 0))
        return e

    def _run(self) -> None:
        mig = pwd = cred = ""
        if self.source == "transfer":
            if not (self._mig.get().strip() and self._pwd.get()):
                return
            mig, pwd = self._mig.get().strip(), self._pwd.get()
        elif self.source == "credential":
            if not self._cred.get().strip():
                return
            cred = self._cred.get().strip()

        self._clear()
        self._title(text.GUI_WORKING_TITLE, text.GUI_WORKING_SUB)
        self._log = ctk.CTkTextbox(self.body, height=180, activate_scrollbars=True)
        self._log.pack(fill="both", expand=True)
        self._log.configure(state="disabled")
        self._result = ctk.CTkFrame(self.body, fg_color="transparent")
        self._result.pack(fill="x", pady=(10, 0))

        threading.Thread(
            target=self._worker, args=(mig, pwd, cred), daemon=True
        ).start()
        self.after(100, self._poll)

    def _worker(self, mig: str, pwd: str, cred: str) -> None:
        echo = lambda s: self.q.put(("log", s))  # noqa: E731
        try:
            with GameClient(self.region) as client:
                if self.source == "steam":
                    _, dest = steam.run(client, self.out_dir, echo=echo)
                elif self.source == "credential":
                    _, dest = credential.run(client, cred, self.out_dir, echo=echo)
                else:
                    _, dest = transfer.run(client, mig, pwd, self.out_dir, echo=echo)
            self.q.put(
                ("done", {"dest": str(dest), "transfer": self.source == "transfer"})
            )
        except Exception as e:  # noqa: BLE001
            self.q.put(("error", str(e)))

    def _poll(self) -> None:
        try:
            while True:
                kind, payload = self.q.get_nowait()
                if kind == "log":
                    self._log.configure(state="normal")
                    self._log.insert("end", payload + "\n")
                    self._log.see("end")
                    self._log.configure(state="disabled")
                elif kind == "done":
                    self._show_done(payload)
                    return
                elif kind == "error":
                    self._show_error(payload)
                    return
        except queue.Empty:
            pass
        self.after(100, self._poll)

    def _show_done(self, info: dict) -> None:
        self._title(text.GUI_DONE_TITLE, text.GUI_DONE_SUB.format(dest=info["dest"]))
        if info.get("transfer"):
            ctk.CTkLabel(
                self._result,
                text=text.GUI_DONE_TRANSFER_NOTE,
                text_color=("gray45", "gray62"),
                wraplength=480,
                justify="left",
            ).pack(anchor="w")
        ctk.CTkLabel(
            self._result,
            text=text.GUI_DONE_UPLOAD,
            text_color=("gray45", "gray62"),
            wraplength=480,
            justify="left",
        ).pack(anchor="w", pady=(10, 0))
        ctk.CTkButton(
            self._result, text=text.GUI_BTN_CLOSE, width=120, command=self.destroy
        ).pack(anchor="e", pady=(12, 0))

    def _show_error(self, msg: str) -> None:
        self._title(text.GUI_ERROR_TITLE, "")
        ctk.CTkLabel(
            self._result,
            text=msg,
            text_color=("#c0392b", "#ff6b5e"),
            wraplength=480,
            justify="left",
        ).pack(anchor="w")
        ctk.CTkButton(
            self._result, text=text.GUI_BTN_BACK, width=120, command=self._step_source
        ).pack(anchor="e", pady=(12, 0))


def run_gui() -> int:
    App().mainloop()
    return 0

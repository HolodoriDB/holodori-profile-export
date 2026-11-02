from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        from .gui import run_gui

        return run_gui()
    from ._cli import run

    return run(argv)


if __name__ == "__main__":
    raise SystemExit(main())

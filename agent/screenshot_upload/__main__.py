"""Uploader-local command line entry point."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .config import RuntimeConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m agent.screenshot_upload")
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (
        ("init", "bind a pristine spool to one Backend origin"),
        ("run", "recover and run the bound upload queue"),
        ("requeue", "explicitly retry one unchanged failed intent"),
    ):
        command = subparsers.add_parser(name, help=help_text)
        command.add_argument("--spool", required=True, type=Path)
        command.add_argument("--backend-origin", required=True)
        if name == "requeue":
            command.add_argument("client_upload_id")
    return parser


def _init(config: RuntimeConfig) -> int:
    from .origin import initialize_binding

    binding = initialize_binding(config.spool_root, config.backend_origin)
    print(f"initialized {config.spool_root} -> {binding.backend_origin}")
    return 0


def _integrated_runtime(config: RuntimeConfig):
    """Load A only when a stateful command is invoked."""

    try:
        from .runtime import build_runtime  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "work-unit A runtime integration is unavailable; parent integration must provide "
            "agent.screenshot_upload.runtime.build_runtime"
        ) from exc
    return build_runtime(config)


def _run(config: RuntimeConfig) -> int:
    runtime = _integrated_runtime(config)
    runtime.run()
    return 0


def _requeue(config: RuntimeConfig, client_upload_id: str) -> int:
    runtime = _integrated_runtime(config)
    runtime.requeue(client_upload_id)
    return 0


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    try:
        config = RuntimeConfig.create(arguments.spool, arguments.backend_origin)
        if arguments.command == "init":
            return _init(config)
        if arguments.command == "run":
            return _run(config)
        return _requeue(config, arguments.client_upload_id)
    except (RuntimeError, ValueError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

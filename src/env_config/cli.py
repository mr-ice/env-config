"""Command-line interface for env-config (scaffold)."""
from __future__ import annotations

import argparse
import os
import sys

from .detect_shell import detect_current_and_intended_shell


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the CLI."""
    p = argparse.ArgumentParser(prog="env-config")
    sub = p.add_subparsers(dest="cmd")

    detect_p = sub.add_parser("detect", help="Detect current and intended shell")
    detect_p.add_argument("--shell", dest="shell", help="Override intended shell (path or name)")
    sub.add_parser("tui", help="Launch TUI (not implemented)")
    disc = sub.add_parser("discover", help="Discover startup files for a shell family")
    disc.add_argument("--family", help="Shell family (bash, zsh, tcsh)")
    disc.add_argument("--shell-path", help="Path to shell executable to use for tracing")
    disc.add_argument(
        "--use-shell-trace",
        action="store_true",
        help="Force shell-level tracing (honors ENVCONFIG_MOCK_TRACE_DIR)",
    )
    disc.add_argument(
        "--refresh-cache",
        action="store_true",
        help="Refresh discovery cache (ignore and remove cached results)",
    )
    disc.add_argument(
        "--existing-only",
        action="store_true",
        help="Only show startup files that currently exist on disk",
    )
    disc.add_argument(
        "--full-paths",
        action="store_true",
        help="Show full absolute paths instead of basenames",
    )
    disc.add_argument(
        "--modes",
        action="store_true",
        help="Show per-invocation-mode discovery (login/interactive combos)",
    )
    disc.add_argument("--tui", action="store_true", help="Show discovery in the TUI")
    trace_p = sub.add_parser(
        "trace", help="Run a shell startup trace and summarize per-file timings"
    )
    trace_p.add_argument("--family", help="Shell family (bash, zsh, tcsh)")
    trace_p.add_argument("--shell-path", help="Path to shell executable to use for tracing")
    trace_p.add_argument(
        "--mode",
        help=(
            "Invocation mode: login_interactive, login_noninteractive, nonlogin_interactive, "
            "nonlogin_noninteractive"
        ),
    )
    trace_p.add_argument(
        "--dry-run", action="store_true", help="Print the tracer command and do not execute it"
    )
    trace_p.add_argument("--output-file", help="Write raw trace output to this file for inspection")
    trace_p.add_argument(
        "--threshold-secs", type=float, help="Flag files taking longer than this many seconds"
    )
    trace_p.add_argument(
        "--threshold-percent",
        type=float,
        help="Flag files taking longer than this percent of total startup time",
    )
    trace_p.add_argument("--tui", action="store_true", help="Show results in a simple TUI")
    trace_p.add_argument(
        "--verbose",
        action="store_true",
        help="Print diagnostic info about detection and command selection",
    )

    config_p = sub.add_parser("config", help="View and edit configuration")
    config_p.add_argument("--tui", action="store_true", help="Open TUI config editor")
    config_sub = config_p.add_subparsers(dest="config_cmd")

    config_sub.add_parser("show", help="Show all config values with defaults")

    get_p = config_sub.add_parser("get", help="Get a config value")
    get_p.add_argument("key", help="Dotted config key (e.g. trace.threshold_secs)")

    set_p = config_sub.add_parser("set", help="Set a config value in user config")
    set_p.add_argument("key", help="Dotted config key")
    set_p.add_argument("value", nargs="+", help="Value to set")
    set_p.add_argument(
        "--append",
        action="store_true",
        help="For list keys, append to existing values instead of replacing",
    )

    reset_p = config_sub.add_parser("reset", help="Reset a config key to default")
    reset_p.add_argument("key", help="Dotted config key to reset")

    # --- backup / archive / restore / list-backups ---
    backup_p = sub.add_parser("backup", help="Back up discovered startup files to a tar.gz archive")
    backup_p.add_argument("--family", help="Shell family (bash, zsh, tcsh)")
    backup_p.add_argument(
        "--include", action="append", default=[], help="Include files matching pattern (repeatable)"
    )
    backup_p.add_argument(
        "--exclude", action="append", default=[], help="Exclude files matching pattern (repeatable)"
    )
    backup_p.add_argument("--tui", action="store_true", help="Interactive file selection TUI")

    archive_p = sub.add_parser("archive", help="Back up startup files and remove originals")
    archive_p.add_argument("--family", help="Shell family (bash, zsh, tcsh)")
    archive_p.add_argument(
        "--include", action="append", default=[], help="Include files matching pattern (repeatable)"
    )
    archive_p.add_argument(
        "--exclude", action="append", default=[], help="Exclude files matching pattern (repeatable)"
    )
    archive_p.add_argument(
        "--yes", action="store_true", help="Skip confirmation before removing originals"
    )
    archive_p.add_argument("--tui", action="store_true", help="Interactive file selection TUI")

    restore_p = sub.add_parser("restore", help="Restore files from a backup archive")
    restore_p.add_argument(
        "--archive",
        dest="archive_substring",
        help="Substring to match archive (default: most recent)",
    )
    restore_p.add_argument(
        "--include", action="append", default=[], help="Include files matching pattern (repeatable)"
    )
    restore_p.add_argument(
        "--exclude", action="append", default=[], help="Exclude files matching pattern (repeatable)"
    )
    restore_p.add_argument(
        "--force", action="store_true", help="Overwrite existing files (default: skip)"
    )
    restore_p.add_argument("--yes", action="store_true", help="Skip confirmation prompt")
    restore_p.add_argument(
        "--tui", action="store_true", help="Interactive archive/file selection TUI"
    )

    sub.add_parser("list-backups", help="List available backup archives")

    return p


def _validate_config_key(key: str) -> bool:
    """Check *key* is in the schema, printing an error if not.

    Returns True when valid, False (with stderr output) when invalid.
    """
    from .config import CONFIG_SCHEMA

    if key in CONFIG_SCHEMA:
        return True
    print(f"error: unknown config key '{key}'", file=sys.stderr)
    print(f"valid keys: {', '.join(sorted(CONFIG_SCHEMA))}", file=sys.stderr)
    return False


def _handle_config_show() -> int:
    """Print all config keys with their merged values."""
    from .config import CONFIG_SCHEMA, config_show

    values = config_show()
    for key in sorted(values):
        meta = CONFIG_SCHEMA[key]
        print(f"{key} = {values[key]!r}  # {meta.description}")
    return 0


def _handle_config_get(key: str) -> int:
    """Print the merged value for a single key."""
    from .config import config_get

    if not _validate_config_key(key):
        return 1
    print(repr(config_get(key)))
    return 0


def _handle_config_set(key: str, raw_values: list[str], append: bool) -> int:
    """Set a config value in the user config file."""
    from .config import CONFIG_SCHEMA, coerce_value, config_set

    if not _validate_config_key(key):
        return 1
    meta = CONFIG_SCHEMA[key]
    try:
        if meta.value_type == "list_of_strings":
            _handle_config_set_list(key, raw_values, append)
        else:
            val = coerce_value(" ".join(raw_values), meta.value_type)
            config_set(key, val)
    except (ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


def _handle_config_set_list(key: str, raw_items: list[str], append: bool) -> None:
    """Set or append a list-of-strings config key."""
    from .config import (
        config_set,
        get_nested,
        load_config,
        save_config,
        set_nested,
        user_config_path,
    )

    if append:
        user_cfg = load_config(user_config_path())
        existing = get_nested(user_cfg, key)
        if not isinstance(existing, list):
            existing = []
        existing.extend(raw_items)
        set_nested(user_cfg, key, existing)
        save_config(user_config_path(), user_cfg)
    else:
        config_set(key, raw_items)


def _handle_config_reset(key: str) -> int:
    """Remove a key from the user config (reverts to default)."""
    from .config import config_reset

    if not _validate_config_key(key):
        return 1
    config_reset(key)
    return 0


def _handle_config(args: argparse.Namespace) -> int:
    """Dispatch ``config`` sub-subcommands (show/get/set/reset/--tui)."""
    if getattr(args, "tui", False):
        try:
            from .tui import display_config_tui

            display_config_tui()
            return 0
        except Exception as exc:
            print(f"TUI failed: {exc}", file=sys.stderr)
            return 1

    config_cmd = getattr(args, "config_cmd", None)
    if config_cmd == "show":
        return _handle_config_show()
    if config_cmd == "get":
        return _handle_config_get(args.key)
    if config_cmd == "set":
        return _handle_config_set(args.key, args.value, getattr(args, "append", False))
    if config_cmd == "reset":
        return _handle_config_reset(args.key)

    print("usage: env-config config {show,get,set,reset} ...", file=sys.stderr)
    return 1


def _resolve_family(args: argparse.Namespace) -> str:
    """Detect and normalize the shell family from CLI args or auto-detection."""
    family = getattr(args, "family", None)
    if not family:
        info = detect_current_and_intended_shell()
        family = info.get("intended_family")
    if isinstance(family, str):
        family = family.lower()
    return family or "bash"


def _discover_files(family: str) -> list[str]:
    """Discover existing startup files for *family* as absolute paths."""
    from .discover import discover_startup_files

    return discover_startup_files(family, existing_only=True, full_paths=True)


_ALL_FAMILIES = ("bash", "zsh", "tcsh")


def _discover_all_families(
    include: list[str] | None = None,
    exclude: list[str] | None = None,
) -> list[tuple[str, list[str]]]:
    """Discover existing startup files for all shell families.

    Parameters
    ----------
    include : list[str] or None
        If set, only keep files matching these fnmatch patterns.
    exclude : list[str] or None
        Remove files matching these fnmatch patterns.

    Returns
    -------
    list[tuple[str, list[str]]]
        Each entry is ``(family, [absolute_paths])``.  Only families
        with at least one file are included.
    """
    from .backup import filter_files

    seen: set[str] = set()
    groups: list[tuple[str, list[str]]] = []
    for fam in _ALL_FAMILIES:
        raw = _discover_files(fam)
        raw = filter_files(raw, include=include, exclude=exclude)
        # Deduplicate across families (e.g. .profile appears in both bash and zsh)
        unique = [f for f in raw if f not in seen]
        seen.update(unique)
        if unique:
            groups.append((fam, unique))
    return groups


def _handle_backup(args: argparse.Namespace) -> int:
    """Handle the ``backup`` subcommand."""
    from .backup import create_backup, filter_files

    family = _resolve_family(args)
    inc = args.include or None
    exc = args.exclude or None

    if getattr(args, "tui", False):
        try:
            from .tui import display_backup_tui

            groups = _discover_all_families(include=inc, exclude=exc)
            if not groups:
                print("no startup files found to back up")
                return 0
            result = display_backup_tui(groups, family, archive_mode=False)
            if result:
                print(f"archive created: {result}")
            return 0
        except Exception as exc_tui:
            print(f"TUI failed: {exc_tui}", file=sys.stderr)
            return 1

    files = _discover_files(family)
    files = filter_files(files, include=inc, exclude=exc)
    if not files:
        print("no startup files found to back up")
        return 0
    print(f"backing up {len(files)} file(s):")
    for f in files:
        print(f"  {f}")
    archive_path = create_backup(files, family)
    print(f"archive created: {archive_path}")
    return 0


def _handle_archive(args: argparse.Namespace) -> int:
    """Handle the ``archive`` subcommand (backup + delete)."""
    from .backup import create_archive, filter_files

    family = _resolve_family(args)
    inc = args.include or None
    exc = args.exclude or None

    if getattr(args, "tui", False):
        try:
            from .tui import display_backup_tui

            groups = _discover_all_families(include=inc, exclude=exc)
            if not groups:
                print("no startup files found to archive")
                return 0
            result = display_backup_tui(groups, family, archive_mode=True)
            if result:
                print(f"archive created: {result}")
            return 0
        except Exception as exc_tui:
            print(f"TUI failed: {exc_tui}", file=sys.stderr)
            return 1

    files = _discover_files(family)
    files = filter_files(files, include=inc, exclude=exc)

    print(f"will back up and remove {len(files)} file(s):")
    for f in files:
        print(f"  {f}")
    if not getattr(args, "yes", False):
        answer = input("Proceed? [y/N] ").strip().lower()
        if answer != "y":
            print("cancelled")
            return 1
    archive_path = create_archive(files, family)
    print(f"archive created: {archive_path}")
    return 0


def _handle_restore(args: argparse.Namespace) -> int:
    """Handle the ``restore`` subcommand."""
    if getattr(args, "tui", False):
        try:
            from .tui import display_restore_tui

            restored = display_restore_tui()
            if restored:
                print(f"restored {len(restored)} file(s)")
            return 0
        except Exception as exc:
            print(f"TUI failed: {exc}", file=sys.stderr)
            return 1

    from .backup import find_archive, list_archives, read_manifest, restore_from_archive

    substring = getattr(args, "archive_substring", None)
    if substring:
        try:
            archive_path = find_archive(substring)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        if archive_path is None:
            print(f"error: no archive matching '{substring}'", file=sys.stderr)
            return 1
    else:
        archives = list_archives()
        if not archives:
            print("error: no backup archives found", file=sys.stderr)
            return 1
        archive_path = archives[0][1]

    manifest = read_manifest(archive_path)
    print(f"archive: {archive_path.name}  ({manifest.timestamp})")
    print(f"files ({len(manifest.files)}):")
    for f in manifest.files:
        print(f"  {f}")

    force = getattr(args, "force", False)
    if not getattr(args, "yes", False):
        action = "restore (overwrite existing)" if force else "restore (skip existing)"
        answer = input(f"{action}? [y/N] ").strip().lower()
        if answer != "y":
            print("cancelled")
            return 1

    restored = restore_from_archive(
        archive_path,
        include=args.include or None,
        exclude=args.exclude or None,
        force=force,
    )
    print(f"restored {len(restored)} file(s)")
    return 0


def _handle_list_backups() -> int:
    """Handle the ``list-backups`` subcommand."""
    from .backup import list_archives, read_manifest

    archives = list_archives()
    if not archives:
        print("no backup archives found")
        return 0
    for timestamp, path in archives:
        try:
            manifest = read_manifest(path)
            file_count = len(manifest.files)
            file_list = ", ".join(manifest.files)
            print(f"{timestamp}  ({file_count} files)  {file_list}")
        except Exception:
            print(f"{timestamp}  {path.name}  (manifest unreadable)")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Command-Line processor for env-config."""
    if argv is None:
        argv = sys.argv[1:]
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.cmd == "detect":
        d = detect_current_and_intended_shell(cli_arg=getattr(args, "shell", None))
        for k, v in d.items():
            print(f"{k}: {v}")
        return 0

    if args.cmd == "tui":
        print("TUI mode not yet implemented")
        return 0

    if args.cmd == "discover":
        from .discover import discover_startup_files, discover_startup_files_modes

        family = getattr(args, "family", None)
        shell_path = getattr(args, "shell_path", None)
        if not family:
            # detect intended shell and use its family when --family omitted
            # pass the provided shell_path as CLI override so detection
            # logic is identical to the `detect` command.
            info = detect_current_and_intended_shell(cli_arg=shell_path)
            family = info.get("intended_family")
            # prefer detected shell path if shell_path not supplied
            if shell_path is None:
                shell_path = info.get("intended_shell")
        # honor CLI flag to force shell-level tracer
        if getattr(args, "use_shell_trace", False):
            os.environ["ENVCONFIG_USE_SHELL_TRACE"] = "1"
        refresh_cache = getattr(args, "refresh_cache", False)
        # normalize family
        if isinstance(family, str):
            family = family.lower()
        if not family:
            family = "bash"
        if getattr(args, "modes", False):
            if refresh_cache:
                from .discover import clear_cache

                clear_cache(family)
            modes = discover_startup_files_modes(
                family,
                shell_path=shell_path,
                existing_only=getattr(args, "existing_only", False),
                full_paths=getattr(args, "full_paths", False),
            )
            if getattr(args, "tui", False):
                try:
                    from .tui import display_discovery_tui

                    display_discovery_tui(modes)
                    return 0
                except Exception as e:
                    print("TUI failed:", e)

            for mode, files in modes.items():
                print(f"== {mode} ==")
                for f in files:
                    print(f)
        else:
            if refresh_cache:
                from .discover import clear_cache

                clear_cache(family)
            files = discover_startup_files(
                family,
                shell_path=shell_path,
                existing_only=getattr(args, "existing_only", False),
                full_paths=getattr(args, "full_paths", False),
            )
            for f in files:
                print(f)
        return 0

    if args.cmd == "trace":
        from .trace import parse_trace, run_shell_trace

        family = getattr(args, "family", None)
        shell_path = getattr(args, "shell_path", None)
        if not family:
            info = detect_current_and_intended_shell(cli_arg=shell_path)
            family = info.get("intended_family")
            if shell_path is None:
                shell_path = info.get("intended_shell")
        # normalize family
        if isinstance(family, str):
            family = family.lower()
        if not family:
            family = "bash"
        mode = getattr(args, "mode", None) or "login_noninteractive"
        # map mode string to args
        mode_map = {
            "login_interactive": ["-l", "-i", "-c", "true"],
            "login_noninteractive": ["-l", "-c", "true"],
            "nonlogin_interactive": ["-i", "-c", "true"],
            "nonlogin_noninteractive": ["-c", "true"],
        }
        args_list = mode_map.get(mode, ["-l", "-c", "true"])
        dry = getattr(args, "dry_run", False)
        out_file = getattr(args, "output_file", None)
        # load merged config defaults when thresholds not specified on CLI
        from .config import load_merged_config

        cfg = load_merged_config()
        thresh_secs = getattr(args, "threshold_secs", None)
        thresh_pct = getattr(args, "threshold_percent", None)
        if thresh_secs is None:
            thresh_secs = cfg.get("trace", {}).get("threshold_secs")
        if thresh_pct is None:
            thresh_pct = cfg.get("trace", {}).get("threshold_percent")

        # Verbose: show detection info and chosen shell/family
        if getattr(args, "verbose", False):
            info = detect_current_and_intended_shell(cli_arg=shell_path)
            print("DETECT:")
            for k, v in info.items():
                print(f"{k}: {v}")
            chosen_shell = shell_path or (
                "bash" if family == "bash" else ("zsh" if family == "zsh" else "tcsh")
            )
            print(f"CHOICE: family={family} shell={chosen_shell}")

        raw = run_shell_trace(
            family, shell_path=shell_path, args=args_list, dry_run=dry, output_file=out_file
        )
        # If dry-run returned a string starting with DRYRUN, print and exit
        if isinstance(raw, str) and raw.startswith("DRYRUN:"):
            print(raw)
            return 0

        parsed = parse_trace(raw, family=family)
        from .trace import analyze_traces

        analysis = analyze_traces(parsed, threshold_secs=thresh_secs, threshold_percent=thresh_pct)

        if getattr(args, "tui", False):
            try:
                from .tui import display_trace_tui

                display_trace_tui(analysis)
                return 0
            except Exception as e:
                print("TUI failed:", e)

        # Print summary
        total = analysis["total"]
        print(f"Total startup duration: {total:.6f}s")
        for item in analysis["items"]:
            flag = "!" if item["flagged"] else " "
            reasons = ",".join(item["reasons"]) if item["reasons"] else ""
            print(
                f"{flag} {item['file']} duration={item['duration']:.6f}s "
                f"cmds={item['commands']} {item['percent']:.1f}% {reasons}"
            )
        return 0

    if args.cmd == "config":
        return _handle_config(args)

    if args.cmd == "backup":
        return _handle_backup(args)
    if args.cmd == "archive":
        return _handle_archive(args)
    if args.cmd == "restore":
        return _handle_restore(args)
    if args.cmd == "list-backups":
        return _handle_list_backups()

    parser.print_help()
    return 0


def _entry() -> None:
    """Console-script entry point (wraps exit code)."""
    raise SystemExit(main())


if __name__ == "__main__":
    _entry()

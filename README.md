# env-config

env-config is a lightweight toolkit to discover, trace, and analyze shell
startup files (bash, zsh, tcsh) so you can find slow or surprising startup
hooks. The project includes safe mock traces and a simple TUI for exploration.

## Quickstart

Install into your environment (editable for development):

```bash
python -m pip install -e .
```

Run the CLI (example):

```bash
env-config detect
env-config discover --family bash --modes
env-config trace --family bash --mode login_noninteractive --dry-run
env-config trace --family bash --mode login_noninteractive --tui
```

Force the safer shell-level tracer (useful on macOS/CI):

```bash
env-config discover --use-shell-trace --modes
```

Clear discovery cache:

```bash
env-config discover --refresh-cache
```

## Environment variables

- `ENVCONFIG_MOCK_TRACE_DIR`: directory of fixture traces used by tests and
  to run the shell-level tracer in mock mode. Point this to
  `tests/fixtures/traces` to reproduce CI/test behavior.
- `ENVCONFIG_USE_SHELL_TRACE`: set to `1`, `true`, or `yes` to force the
  shell-level tracer instead of system tracers like `strace`.
- `ENVCONFIG_CACHE_DIR`: overrides the cache directory used by discovery.

## CLI highlights

- `detect` — detect current and intended shell and family. See
  [src/env_config/detect_shell.py](src/env_config/detect_shell.py)
- `discover` — discover candidate startup files (per-mode or union). Flags:
  `--family`, `--shell-path`, `--use-shell-trace`, `--refresh-cache`,
  `--modes`. See [src/env_config/discover.py](src/env_config/discover.py).
- `trace` — run a shell-level trace and summarize per-file timing. Flags:
  `--family`, `--shell-path`, `--mode`, `--dry-run`, `--output-file`,
  `--threshold-secs`, `--threshold-percent`, `--tui`. Core tracing/parsing is in
  [src/env_config/trace.py](src/env_config/trace.py).

## Testing

Run the test suite with the correct PYTHONPATH (the Makefile target wraps
this for convenience):

```bash
make test
# or
PYTHONPATH=src pytest -q
```

The tests use mock trace fixtures under `tests/fixtures/traces`; to run the
discovery/trace code paths using these fixtures set `ENVCONFIG_MOCK_TRACE_DIR`.

## Development notes

- Parsers: `src/env_config/trace.py` contains parsers for bash, zsh, tcsh and
  a generic fallback. Improve path normalization and timestamp extraction
  there when adding new fixtures.
- Discovery: `src/env_config/discover.py` prefers system tracers where
  available but falls back to the safer shell-level tracer which honors the
  mock fixtures. The cache directory defaults to `~/.cache/env-config` but
  can be overridden with `ENVCONFIG_CACHE_DIR`.
- TUI: a simple curses UI lives in `src/env_config/tui.py`.

If you'd like, I can expand the README with examples showing how to use the
TUI interactively and a recommended workflow for safely creating and testing
custom startup scripts.
# env-config

env-config is a developer/operator tool to inspect and manage shell
startup files (login/profile/rc files), back them up, and initialize
user environments from a repository.

Current implemented features (prototype)

- `detect`: determine current/login shell and intended shell using:
  - login shell from the passwd entry
  - `$SHELL` environment variable
  - parent process name
  - optional CLI override `--shell`

- `discover`: best-effort discovery of startup files used by shell
  families. Provides a fallback curated list and a tracer-backed
  discovery mode (if `strace` present). Use `--modes` to list files
  for four invocation modes: `login_interactive`, `login_noninteractive`,
  `nonlogin_interactive`, `nonlogin_noninteractive`.

- `trace`: run a non-privileged shell-level trace to capture which
  startup files are sourced and approximate time spent in each file.
  - Supports `bash`, `zsh`, and `tcsh` families.
  - Uses `BASH_XTRACEFD` + `PS4` for `bash` to capture timestamps.
  - Uses `-x` capture of stderr for `zsh`/`tcsh` and best-effort parsing.
  - Analyze results to compute per-file duration and percent of total.
  - Thresholds: `--threshold-secs` and `--threshold-percent` to flag slow files.
  - `--dry-run` prints the command without executing.
  - `--output-file` saves raw trace output for inspection.
  - `--tui` opens a minimal curses UI to inspect flagged files.

Configuration

Global config: `/etc/env-config.json` (optional)
User config: `~/.env-config.json` (optional)

Config keys of interest (example):

```json
{
  "trace": { "threshold_secs": 0.05, "threshold_percent": 10.0 },
  "tui": { "page_size": 20 }
}
```

The CLI merges global and user configs; user values override global ones.

Safety and notes

- The tracer runs the user's shell and will execute startup files. By
  default the invocation uses `-c true` to exit after startup, but the
  startup files are still executed — run on a safe/test account if you
  are worried about side-effects.
- The syscall-level tracing (strace/eBPF/DTrace) is not used by default
  because it can require privileges. The shell-level approach is
  portable and non-privileged and typically identifies slow shell
  plugins and initialization commands which are the primary operator
  complaints.

Development / usage

Install test deps and run tests:

```bash
python -m pip install -U pytest
make test
```

Basic CLI examples

```bash
# detect
PYTHONPATH=src python -m env_config.cli detect

# discover (per-mode)
PYTHONPATH=src python -m env_config.cli discover --family bash --modes

# run a trace and print a summary
PYTHONPATH=src python -m env_config.cli trace --family bash --mode login_noninteractive --threshold-secs 0.05

# run trace and open curses TUI
PYTHONPATH=src python -m env_config.cli trace --family bash --mode login_noninteractive --threshold-secs 0.05 --tui

# dry-run to view command
PYTHONPATH=src python -m env_config.cli trace --family zsh --mode login_noninteractive --dry-run
```

Next features to implement

- Backup/archive/restore and repo init/install.
- Full TUI workflow for backup/restore and file selection.
- Additional shell-family improvements and safer tracer mocks for CI.

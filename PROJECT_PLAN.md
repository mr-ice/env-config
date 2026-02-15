# Implementation Plan

This document outlines the detailed implementation plan derived from PROJECT.md.

1. Core scaffolding
   - Create Python package layout, CLI entrypoint, basic modules, tests, Makefile.
2. Feature 1: Shell detection
   - Implement detection of loginShell, parent process, SHELL env and CLI override.
   - Unit tests for detection precedence and edge cases.
3. Feature 2: Startup-file discovery
   - Implement invocation tracing strategy (linux: strace; macOS: dtruss/truss fallback) with safe dry-run.
   - Cache discovered files and present CLI/TUI listing.
4. Feature 3: Config system
   - Global and per-user config files, defaults, edit CLI/TUI.
5. Backup/Archive/Restore
   - Implement backup, archive (compress+delete), restore with filters and archive selection logic.
6. Repo handling and init
   - Implement clone/pull/verification logic with operator prompts.
7. Optional curated files
   - Registry for optional files, selection UI, install semantics.
8. Update action
   - Sync files from remotes and repo; registry-based updates.
9. TUI
   - Implement textual/curses-based TUI with parity to CLI.
10. Tests and CI
   - Unit tests for each module, integration tests for workflows; add CI pipeline.

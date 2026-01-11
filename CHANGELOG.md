# Changelog

All notable changes to this repository will be documented here.

## [2024-12-04] Capture HAM
- Added an EchoLink-backed HAM capture service and N5OAK profile that lean on the core capture agent.

## [2024-11-29] Ruff refresh
- Updated Ruff to v0.14.8 in both `pyproject.toml` and pre-commit configuration to match upstream tooling.

## [2024-11-28] Tooling alignment
- Bumped Ruff to the latest release across `pyproject.toml` and pre-commit to match current local tooling.
- Clarified Python runtime expectations (3.11–3.12) and version-bump policy in AGENTS/AI guide.
- Reinforced LF-only defaults and repo-pinned tooling guidance for contributors.

## [2024-11-27] Guidance refresh
- Added AGENTS.md files to capture repository-specific AI guardrails.
- Introduced AI-guided checklist, roadmap, and VS Code settings for consistent tooling.
- Added pre-commit configuration and helper script for repeatable local checks.
- Aligned Ruff versions across pyproject and pre-commit, reinforced LF-only editing defaults, and relaxed the dev check script for Docker friendliness.

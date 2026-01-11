# AI-guided coding checklist

Use this checklist before submitting automated changes. It complements `AGENTS.md` and `coding_rules.txt`.

1. **Clarify scope** – Identify the service touched (capture, web, transcribe, shared code, or UI), check for nested AGENTS.md files, and avoid back-and-forth questions when the target is already known.
2. **Plan the smallest diff** – Prefer targeted edits; avoid refactors that cross service boundaries unless required, and choose patterns that are easy to upgrade later.
3. **Keep data models aligned** – Use shared payload helpers (`services/common/shared_code` and web `app/` utilities) instead of redefining schemas.
4. **Respect deployment paths** – New assets or scripts should keep Docker Compose mount points and `services/web/static` expectations intact.
5. **Validate locally** – Run `uv run pre-commit run --all-files`; add pytest/Vite checks relevant to the touched code paths. Keep Ruff aligned with the repo-pinned version (currently 0.14.8) when installing locally.
6. **Document impacts** – Note env var changes, new ports, or migrations in README + CHANGELOG. Only bump version numbers when the change is substantial (roughly 100+ lines or cross-service refactors).
7. **Security sanity** – Never log secrets; keep API key enforcement optional but well-tested when enabled.

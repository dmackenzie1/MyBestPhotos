# Branch Intent — 2026-04-22 — Fix app client `ImportMeta.env` typing

## Intent
Resolve persistent TypeScript build failures in the app client where `import.meta.env` is reported as missing on `ImportMeta` during workspace Docker/client builds.

## Scope
- Add explicit Vite client types to the app client TypeScript config.
- Keep existing `PHOTO_ROOT_1..3` compose mounts and `PHOTO_ROOTS_JSON` wiring unchanged.

## Architecture decisions
- Use `compilerOptions.types` in `services/app/client/tsconfig.json` to load `vite/client` explicitly.
- Keep `src/vite-env.d.ts` in place as a local ambient reference for tooling consistency.

## What went right
- The failure mode was isolated to TypeScript ambient type loading, not runtime code paths.
- Root/env wiring for photo sources already existed and needed no functional changes.

## What went wrong
- Initial assumption that only `vite-env.d.ts` was enough did not satisfy the reported persistent failure scenario.

## Validation
- Verified `PHOTO_ROOT_1..3` and `PHOTO_ROOTS_JSON` are still present in `docker-compose.yml`.
- Attempted local npm validation, but package registry access is blocked in this environment.

## Follow-ups
- Re-run the Docker build in an environment with Docker/npm registry access to confirm end-to-end success.
- If the error persists, capture full `tsc --showConfig` output from inside the build container.

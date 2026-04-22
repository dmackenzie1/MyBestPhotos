# UI Component and Style Rules

These rules keep the client maintainable as screens grow.

## Component structure
- Each visual unit should live in its own file under `src/ui/components/`.
- Keep `App.tsx` focused on orchestration (state, data loading, view routing), not detailed JSX markup.
- Shared helpers belong in `src/ui/lib/`.
- Shared view/data types belong in `src/ui/types.ts`.

## Styling structure
- Keep global variables/layout primitives in `src/styles.css` only.
- Every component owns a stylesheet under `src/ui/styles/<component>.css`.
- Component files must import their own stylesheet.
- Reuse CSS variables from `:root` rather than hardcoding duplicate palettes where practical.

## Naming
- Use PascalCase for components, kebab-case for css filenames.
- Keep class names descriptive and aligned to component purpose.

## Scope guard
- New browse/timeline/settings UI additions should follow this split by default.

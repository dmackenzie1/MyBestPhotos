/**
 * Build note:
 * Docker image builds can fail with:
 *   TS7016: Could not find a declaration file for module 'pg'
 * This local declaration keeps strict builds unblocked when @types/pg
 * is not available in the build environment.
 */
declare module "pg";

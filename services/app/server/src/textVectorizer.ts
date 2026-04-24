const TOKEN_RE = /[a-z0-9]+/g;
export const DEFAULT_DIM = 384;

export function tokenizeText(text: string): string[] {
  return (text.toLowerCase().match(TOKEN_RE) ?? []).filter(Boolean);
}

function hashToken(token: string): Uint8Array {
  let hash = 2166136261;
  for (let i = 0; i < token.length; i += 1) {
    hash ^= token.charCodeAt(i);
    hash = Math.imul(hash, 16777619);
  }
  const bytes = new Uint8Array(8);
  for (let i = 0; i < 8; i += 1) {
    bytes[i] = (hash >>> ((i % 4) * 8)) & 0xff;
  }
  return bytes;
}

export function embedText(text: string, dim = DEFAULT_DIM): number[] {
  const tokens = tokenizeText(text);
  if (!tokens.length) return Array.from({ length: dim }, () => 0);
  const vector = Array.from({ length: dim }, () => 0);
  for (const token of tokens) {
    const bytes = hashToken(token);
    const slot = (((bytes[0] << 24) | (bytes[1] << 16) | (bytes[2] << 8) | bytes[3]) >>> 0) % dim;
    const sign = bytes[4] % 2 ? -1 : 1;
    const weight = 1 + Math.min(token.length, 12) / 12;
    vector[slot] += sign * weight;
  }
  const norm = Math.sqrt(vector.reduce((sum, value) => sum + value * value, 0));
  if (norm <= 1e-9) return Array.from({ length: dim }, () => 0);
  return vector.map((value) => value / norm);
}

export function vectorLiteral(values: number[]): string {
  return `[${values.map((value) => value.toFixed(8)).join(",")}]`;
}

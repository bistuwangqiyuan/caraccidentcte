/** Simple in-memory IP rate limit (per serverless instance). */
const hits = new Map<string, { n: number; reset: number }>();

export function rateLimit(key: string, limit = 20, windowMs = 60_000): boolean {
  const now = Date.now();
  const cur = hits.get(key);
  if (!cur || now > cur.reset) {
    hits.set(key, { n: 1, reset: now + windowMs });
    return true;
  }
  if (cur.n >= limit) return false;
  cur.n += 1;
  return true;
}

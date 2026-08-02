import { createHmac, timingSafeEqual } from "crypto";

const COOKIE = "aftercrash_unlock";
const MAX_AGE_SEC = 60 * 60 * 24 * 7; // 7 days

function secret(): string {
  const s = process.env.UNLOCK_SECRET;
  if (!s) throw new Error("UNLOCK_SECRET is not configured");
  return s;
}

export function signUnlock(sessionId: string, exp: number): string {
  const payload = `${sessionId}.${exp}`;
  const sig = createHmac("sha256", secret()).update(payload).digest("base64url");
  return `${payload}.${sig}`;
}

export function verifyUnlockToken(token: string | undefined): boolean {
  if (!token) return false;
  const parts = token.split(".");
  if (parts.length !== 3) return false;
  const [sessionId, expStr, sig] = parts;
  const exp = Number(expStr);
  if (!sessionId || !Number.isFinite(exp) || Date.now() / 1000 > exp) return false;
  const expected = createHmac("sha256", secret())
    .update(`${sessionId}.${exp}`)
    .digest("base64url");
  try {
    const a = Buffer.from(sig);
    const b = Buffer.from(expected);
    if (a.length !== b.length) return false;
    return timingSafeEqual(a, b);
  } catch {
    return false;
  }
}

export function unlockCookieOptions(token: string) {
  return {
    name: COOKIE,
    value: token,
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax" as const,
    path: "/",
    maxAge: MAX_AGE_SEC,
  };
}

export { COOKIE as UNLOCK_COOKIE, MAX_AGE_SEC };

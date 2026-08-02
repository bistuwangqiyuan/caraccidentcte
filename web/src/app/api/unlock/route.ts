import { NextRequest, NextResponse } from "next/server";
import { UNLOCK_COOKIE, verifyUnlockToken } from "@/lib/unlock";

export async function GET(req: NextRequest) {
  const token = req.cookies.get(UNLOCK_COOKIE)?.value;
  let unlocked = false;
  try {
    unlocked = verifyUnlockToken(token);
  } catch {
    unlocked = false;
  }
  return NextResponse.json({ unlocked });
}

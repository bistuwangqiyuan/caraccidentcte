import type { PackState } from "../../content/checklist";
import { emptyPack } from "../../content/checklist";

const KEY = "aftercrash_pack_v1";

export function loadPack(): PackState {
  if (typeof window === "undefined") return emptyPack();
  try {
    const raw = sessionStorage.getItem(KEY);
    if (!raw) return emptyPack();
    return { ...emptyPack(), ...JSON.parse(raw) };
  } catch {
    return emptyPack();
  }
}

export function savePack(state: PackState): void {
  if (typeof window === "undefined") return;
  sessionStorage.setItem(KEY, JSON.stringify(state));
}

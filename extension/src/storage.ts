import { IS_WEBSITE } from "./lib/runtime";

// Falls back to localStorage when running via `npm run dev` in a normal
// browser tab (chrome.storage only exists inside an actual extension).
const hasChromeStorage = !IS_WEBSITE && typeof chrome !== "undefined" && !!chrome.storage?.local;

const sensitiveDrafts = new Set(["codestreak_draft_password", "codestreak_draft_new_password", "codestreak_draft_otp"]);

export async function getStored(key: string): Promise<string | null> {
  if (IS_WEBSITE && sensitiveDrafts.has(key)) { localStorage.removeItem(key); return null; }
  if (hasChromeStorage) {
    return new Promise((resolve) => {
      chrome.storage.local.get([key], (result) => resolve(result[key] ?? null));
    });
  }
  return localStorage.getItem(key);
}

export async function setStored(key: string, value: string): Promise<void> {
  if (IS_WEBSITE && sensitiveDrafts.has(key)) return;
  if (hasChromeStorage) {
    return new Promise((resolve) => {
      chrome.storage.local.set({ [key]: value }, () => resolve());
    });
  }
  localStorage.setItem(key, value);
}

export async function clearStored(keys: string[]): Promise<void> {
  if (hasChromeStorage) {
    return new Promise((resolve) => {
      chrome.storage.local.remove(keys, () => resolve());
    });
  }
  keys.forEach((k) => localStorage.removeItem(k));
}

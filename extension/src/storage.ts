// Falls back to localStorage when running via `npm run dev` in a normal
// browser tab (chrome.storage only exists inside an actual extension).
const sensitiveDrafts = new Set(["codestreak_draft_password", "codestreak_draft_new_password", "codestreak_draft_otp"]);
const hasChromeStorage = typeof chrome !== "undefined" && !!chrome.storage?.local;

export async function getStored(key: string): Promise<string | null> {
  if (sensitiveDrafts.has(key)) { await clearStored([key]); return null; }
  if (hasChromeStorage) {
    return new Promise((resolve, reject) => {
      chrome.storage.local.get([key], (result) => {
        const error = chrome.runtime.lastError;
        if (error) reject(new Error(error.message || "Could not read device storage."));
        else resolve(result[key] ?? null);
      });
    });
  }
  return localStorage.getItem(key);
}

export async function setStored(key: string, value: string): Promise<void> {
  if (sensitiveDrafts.has(key)) return;
  if (hasChromeStorage) {
    return new Promise((resolve, reject) => {
      chrome.storage.local.set({ [key]: value }, () => {
        const error = chrome.runtime.lastError;
        if (error) reject(new Error(error.message || "Could not save device storage."));
        else resolve();
      });
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

// Browser-only state for the website. Credentials and reset codes stay in memory.
const sensitiveDrafts = new Set(["codestreak_draft_password", "codestreak_draft_new_password", "codestreak_draft_otp"]);

export async function getStored(key: string): Promise<string | null> {
  if (sensitiveDrafts.has(key)) {
    localStorage.removeItem(key);
    return null;
  }
  return localStorage.getItem(key);
}

export async function setStored(key: string, value: string): Promise<void> {
  if (!sensitiveDrafts.has(key)) localStorage.setItem(key, value);
}

export async function clearStored(keys: string[]): Promise<void> {
  keys.forEach((key) => localStorage.removeItem(key));
}

// Falls back to localStorage when running via `npm run dev` in a normal
// browser tab (chrome.storage only exists inside an actual extension).
const sensitiveDrafts = new Set(["codestreak_draft_password", "codestreak_draft_new_password", "codestreak_draft_otp"]);
const hasChromeStorage = typeof chrome !== "undefined" && !!chrome.storage?.local;

export async function getStored(key: string): Promise<string | null> {
  if (sensitiveDrafts.has(key)) { await clearStored([key]); return null; }
  if (hasChromeStorage) {
    return new Promise((resolve) => {
      chrome.storage.local.get([key], (result) => resolve(result[key] ?? null));
    });
  }
  return localStorage.getItem(key);
}

export async function setStored(key: string, value: string): Promise<void> {
  if (sensitiveDrafts.has(key)) return;
  if (hasChromeStorage) {
    return new Promise((resolve) => {
      chrome.storage.local.set({ [key]: value }, () => resolve());
    });
  }
  localStorage.setItem(key, value);
}

export const SESSION_STORAGE_KEY = "codestreak_session_v2";

export interface StoredSession {
  version: 2;
  userId: number;
  accessToken: string;
}

export async function clearStored(keys: string[]): Promise<void> {
  if (hasChromeStorage) {
    return new Promise((resolve) => {
      chrome.storage.local.remove(keys, () => resolve());
    });
  }
  keys.forEach((k) => localStorage.removeItem(k));
}

/**
 * Reads the active authenticated session, migrating legacy storage keys if necessary.
 */
export async function getStoredSession(): Promise<StoredSession | null> {
  // 1. Try modern versioned session key
  const rawV2 = await getStored(SESSION_STORAGE_KEY);
  if (rawV2) {
    try {
      const parsed = JSON.parse(rawV2);
      if (
        parsed &&
        parsed.version === 2 &&
        Number.isSafeInteger(parsed.userId) &&
        parsed.userId > 0 &&
        typeof parsed.accessToken === "string" &&
        parsed.accessToken
      ) {
        return parsed as StoredSession;
      }
    } catch (_) {}
  }

  // 2. Migration: check individual keys
  const userIdStr = await getStored("codestreak_user_id");
  const token = await getStored("codestreak_access_token");
  if (userIdStr && token) {
    const userId = parseInt(userIdStr, 10);
    if (Number.isSafeInteger(userId) && userId > 0) {
      const migrated: StoredSession = { version: 2, userId, accessToken: token };
      await setStoredSession(migrated);
      return migrated;
    }
  }

  // 3. Migration: check legacy codestreak_user object
  const legacyUserRaw = await getStored("codestreak_user");
  if (legacyUserRaw) {
    try {
      const legacyUser = JSON.parse(legacyUserRaw);
      const uid = legacyUser?.id ?? legacyUser?.user_id;
      const tok = legacyUser?.token ?? legacyUser?.access_token ?? token;
      if (Number.isSafeInteger(uid) && uid > 0 && typeof tok === "string" && tok) {
        const migrated: StoredSession = { version: 2, userId: uid, accessToken: tok };
        await setStoredSession(migrated);
        return migrated;
      }
    } catch (_) {}
  }

  return null;
}

/**
 * Stores the authenticated session under the versioned key and synchronizes individual keys.
 */
export async function setStoredSession(session: StoredSession): Promise<void> {
  const json = JSON.stringify(session);
  await setStored(SESSION_STORAGE_KEY, json);
  await setStored("codestreak_user_id", String(session.userId));
  await setStored("codestreak_access_token", session.accessToken);
}

/**
 * Clears the session and invalidates account-scoped caches.
 */
export async function clearStoredSession(): Promise<void> {
  const currentSession = await getStoredSession();
  const keysToRemove = [
    SESSION_STORAGE_KEY,
    "codestreak_user_id",
    "codestreak_access_token",
    "codestreak_user",
    "codestreak_cached_dash",
    "codestreak_cached_board",
    "codestreak_active_tab"
  ];
  if (currentSession?.userId) {
    keysToRemove.push(
      `codestreak_menu_${currentSession.userId}`,
      `codestreak_startup_tab_${currentSession.userId}`
    );
  }
  await clearStored(keysToRemove);
}

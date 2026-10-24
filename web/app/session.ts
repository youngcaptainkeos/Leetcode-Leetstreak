import { useSyncExternalStore } from "react";

const SESSION_KEY = "codestreak_user_id";
const SESSION_EVENT = "leetstreak:session";

export function getSessionUserId(): number | null {
  const stored = localStorage.getItem(SESSION_KEY);
  const id = stored ? Number(stored) : NaN;
  return Number.isSafeInteger(id) && id > 0 ? id : null;
}

export function setSessionUserId(id: number | null): void {
  if (id !== null && (!Number.isSafeInteger(id) || id <= 0)) throw new Error("Invalid account ID");
  // Account-specific caches and unfinished form drafts must not survive sign-out.
  if (id === null || id !== getSessionUserId()) {
    Object.keys(localStorage).filter(key => key.startsWith("codestreak_")).forEach(key => localStorage.removeItem(key));
  }
  if (id === null) localStorage.removeItem(SESSION_KEY);
  else localStorage.setItem(SESSION_KEY, String(id));
  window.dispatchEvent(new Event(SESSION_EVENT));
}

function subscribeSession(listener: () => void): () => void {
  const onStorage = (event: StorageEvent) => {
    if (event.key === SESSION_KEY || event.key === null) listener();
  };
  window.addEventListener(SESSION_EVENT, listener);
  window.addEventListener("storage", onStorage);
  return () => {
    window.removeEventListener(SESSION_EVENT, listener);
    window.removeEventListener("storage", onStorage);
  };
}

export function useSessionUserId(): number | null {
  return useSyncExternalStore(subscribeSession, getSessionUserId, () => null);
}

export function navigate(path: string, replace = false): void {
  if (window.location.pathname + window.location.hash === path) return;
  const previousPath = window.location.pathname;
  window.history[replace ? "replaceState" : "pushState"](null, "", path);
  if (window.location.pathname !== previousPath) window.scrollTo(0, 0);
  window.dispatchEvent(new PopStateEvent("popstate"));
}

function subscribePath(listener: () => void): () => void {
  window.addEventListener("popstate", listener);
  return () => window.removeEventListener("popstate", listener);
}

export function usePathname(): string {
  return useSyncExternalStore(subscribePath, () => window.location.pathname, () => "/");
}

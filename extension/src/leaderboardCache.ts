import { api, LeaderboardResponse } from "./lib/api";
import { getStored, setStored, clearStored } from "./storage";

export type BoardTab = "global" | "friends" | number;
export type BoardSort = "points" | "streak";
type CachedBoard = { board: LeaderboardResponse; savedAt: number };
const FRESH_MS = 60_000;
const memory = new Map<string, CachedBoard>();
const epochs = new Map<number, number>();
const pending = new Map<string, { epoch: number; promise: Promise<LeaderboardResponse> }>();
export const boardMemoryKey = (tab: BoardTab, sort: BoardSort) => `${tab}:${sort}`;
export const boardStorageKey = (userId: number, tab: BoardTab, sort: BoardSort) =>
  `codestreak_board_v3_${userId}_${boardMemoryKey(tab, sort)}`;
const epochKey = (userId: number) => `codestreak_board_epoch_${userId}`;

async function epochFor(userId: number) {
  if (!epochs.has(userId)) {
    const saved = Number(await getStored(epochKey(userId)).catch(() => null));
    // An invalidation during the storage read must win over the saved value.
    if (!epochs.has(userId)) epochs.set(userId, Number.isFinite(saved) ? saved : 0);
  }
  return epochs.get(userId)!;
}

export function peekBoard(userId: number, tab: BoardTab, sort: BoardSort) {
  return memory.get(boardStorageKey(userId, tab, sort))?.board;
}

export async function readCachedBoard(userId: number, tab: BoardTab, sort: BoardSort): Promise<CachedBoard | null> {
  const key = boardStorageKey(userId, tab, sort);
  if (memory.has(key)) return memory.get(key)!;
  const raw = await getStored(key).catch(() => null);
  if (memory.has(key)) return memory.get(key)!;
  try {
    if (raw) {
      const value: CachedBoard = JSON.parse(raw);
      if (Array.isArray(value.board?.entries) && Number.isFinite(value.savedAt)) {
        memory.set(key, value);
        return value;
      }
    }
    // v2 caches were already scoped correctly, but lack a freshness timestamp.
    const legacy = await getStored(`codestreak_board_v2_${userId}_${boardMemoryKey(tab, sort)}`).catch(() => null);
    if (memory.has(key)) return memory.get(key)!;
    if (legacy) {
      const board: LeaderboardResponse = JSON.parse(legacy);
      if (Array.isArray(board.entries)) {
        const value = { board, savedAt: 0 };
        memory.set(key, value);
        return value;
      }
    }
  } catch { /* A corrupt cache is replaceable; never use another view's data. */ }
  return null;
}

export function saveBoard(userId: number, tab: BoardTab, sort: BoardSort, board: LeaderboardResponse) {
  const value = { board, savedAt: Date.now() };
  const key = boardStorageKey(userId, tab, sort);
  memory.set(key, value);
  void setStored(key, JSON.stringify(value)).catch(() => undefined);
}

export function invalidateBoards(userId: number) {
  const epoch = Math.max(Date.now(), (epochs.get(userId) ?? 0) + 1);
  epochs.set(userId, epoch);
  void setStored(epochKey(userId), String(epoch)).catch(() => undefined);
}

export function forgetGroupBoard(userId: number, tab: number) {
  invalidateBoards(userId);
  const keys = (["points", "streak"] as const).flatMap(sort => {
    const key = boardStorageKey(userId, tab, sort);
    memory.delete(key);
    return [key, `codestreak_board_v2_${userId}_${boardMemoryKey(tab, sort)}`];
  });
  void clearStored(keys).catch(() => undefined);
}

export async function loadBoard(userId: number, tab: BoardTab, sort: BoardSort, force = false) {
  const cached = await readCachedBoard(userId, tab, sort);
  const epoch = await epochFor(userId);
  const age = cached ? Date.now() - cached.savedAt : Infinity;
  if (!force && cached && cached.savedAt >= epoch && age >= 0 && age < FRESH_MS) return cached.board;
  const key = boardStorageKey(userId, tab, sort);
  const existing = pending.get(key);
  if (existing?.epoch === epoch) return existing.promise;
  const promise = (async () => {
    const board = await (tab === "global" ? api.leaderboard(userId, sort)
      : tab === "friends" ? api.friendsLeaderboard(userId, sort)
      : api.groupLeaderboard(tab, userId, sort));
    // Cache a valid result even after the user switches away. A response from
    // before Sync/a membership change must not replace the newer cache.
    if (epochs.get(userId) === epoch) saveBoard(userId, tab, sort, board);
    return board;
  })();
  pending.set(key, { epoch, promise });
  try { return await promise; }
  finally { if (pending.get(key)?.promise === promise) pending.delete(key); }
}

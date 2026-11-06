import { useEffect, useRef, useState } from "react";
import { api, ApiError } from "../lib/api";
import { getStored, setStored } from "../storage";
import { ProgressState, StudyPlan, addStudyPlan, removeStudyPlan, restoreStarterPlans, readProgress, progressKey } from "./data";

type Operation = { operation_id: string; kind: string; data: Record<string, unknown> };
type SavedProgress = Awaited<ReturnType<typeof api.getProgress>>;
const id = () => crypto.randomUUID();

function apply(state: ProgressState, operation: Operation): ProgressState {
  const { kind, data } = operation;
  if (kind === "initialize") return state;
  if (kind === "add") return addStudyPlan(state, data.plan as unknown as StudyPlan);
  if (kind === "remove") return removeStudyPlan(state, data.slug as string);
  if (kind === "restore") return restoreStarterPlans(state);
  if (kind === "follow" || kind === "manual") {
    const field = kind === "follow" ? "followed" : "manual";
    const next = state[field].filter(slug => slug !== data.slug);
    return { ...state, [field]: data.enabled ? [...next, data.slug as string] : next };
  }
  if (kind === "observe") return { ...state, observed: [...new Set([...state.observed, ...data.slugs as string[]])], lastFullSyncAt: typeof data.syncedAt === "number" ? Math.max(state.lastFullSyncAt || 0, data.syncedAt) : state.lastFullSyncAt };
  return state;
}

class AccountPlanSync {
  private queue: Operation[] = [];
  private remote = readProgress(null);
  private initial = this.remote;
  private version = 0;
  private alive = true;
  private running = false;
  private loadedServer = false;
  private leetcodeVersion: number | null = null;
  private token: string | null = null;
  private writes = Promise.resolve();
  private cacheKey: string;
  private outboxKey: string;
  private originalKey: string;

  constructor(private userId: number, private username: string, private onState: (state: ProgressState) => void, private onStatus: (status: string) => void) {
    this.cacheKey = progressKey(userId, username);
    this.outboxKey = `${this.cacheKey}_account_outbox`;
    this.originalKey = `${this.cacheKey}_before_account_sync`;
  }

  stop() { this.alive = false; }
  private persist() {
    const queue = JSON.stringify(this.queue);
    const state = JSON.stringify(this.queue.reduce(apply, this.remote));
    this.writes = this.writes.catch(() => {}).then(async () => {
      await setStored(this.outboxKey, queue);
      await setStored(this.cacheKey, state);
    });
    return this.writes;
  }
  private publish() {
    if (this.alive) this.onState(this.queue.reduce(apply, this.remote));
  }
  private accept(saved: SavedProgress) {
    this.version = saved.version;
    this.leetcodeVersion = typeof saved.state.leetcodeVersion === "number" ? saved.state.leetcodeVersion : null;
    this.queue = this.queue.filter(op => op.kind !== "observe" || op.data.accountVersion === this.leetcodeVersion);
    this.remote = readProgress(JSON.stringify(saved.state));
    this.loadedServer = true;
  }
  private async signedIn() {
    return this.alive && this.token !== null && await getStored("codestreak_access_token") === this.token && await getStored("codestreak_user_id") === String(this.userId);
  }
  async start() {
    try {
      const [raw, queued, token, backup] = await Promise.all([getStored(this.cacheKey), getStored(this.outboxKey), getStored("codestreak_access_token"), getStored(this.originalKey)]);
      if (!this.alive) return;
      this.token = token;
      this.remote = this.initial = readProgress(raw);
      if (raw && backup === null) await setStored(this.originalKey, raw);
      try {
        const parsed = JSON.parse(queued || "[]");
        if (Array.isArray(parsed)) this.queue = parsed.filter((op): op is Operation => op && /^[a-zA-Z0-9-]{16,80}$/.test(op.operation_id) && ["initialize", "add", "remove", "restore", "follow", "manual", "observe"].includes(op.kind) && op.data && typeof op.data === "object");
      } catch { this.onStatus("Saved changes could not be read. Your local library is retained."); }
      this.publish();
      await this.refresh();
    } catch {
      if (this.alive) this.onStatus("Device storage is unavailable. Changes cannot be saved yet.");
    }
  }
  mutate(kind: string, data: Record<string, unknown>) {
    if (!this.alive) return;
    if (kind === "observe") {
      if (this.leetcodeVersion === null) return;
      data = { ...data, accountVersion: this.leetcodeVersion };
      const projected = this.queue.reduce(apply, this.remote);
      const slugs = data.slugs as string[];
      if (slugs.every(slug => projected.observed.includes(slug)) && (!data.syncedAt || Number(data.syncedAt) <= (projected.lastFullSyncAt || 0))) return;
    }
    this.queue.push({ operation_id: id(), kind, data });
    this.publish();
    this.onStatus("Changes saved on this device · waiting to sync");
    void this.persist().then(() => this.refresh()).catch(() => {
      if (this.alive) this.onStatus("Device storage is full. Keep this window open and retry saving.");
    });
  }
  async refresh() {
    if (this.running) return;
    this.running = true;
    try {
      if (!await this.signedIn()) return;
      await this.writes;
      const saved = await api.getProgress(this.userId);
      if (!await this.signedIn()) return;
      this.accept(saved);
      if (!saved.initialized && !this.queue.some(op => op.kind === "initialize")) {
        // Only the first successful account initialization imports a local
        // snapshot. Other devices cannot resurrect removed plans from caches.
        this.queue.unshift({ operation_id: id(), kind: "initialize", data: { customPlans: this.initial.customPlans, hiddenPlans: this.initial.hiddenPlans, followed: this.initial.followed, manual: this.initial.manual, observed: this.initial.observed } });
        await this.persist();
      }
      this.publish();
      let conflicts = 0;
      let rejected = "";
      while (this.queue.length && await this.signedIn()) {
        const operation = this.queue[0];
        try {
          const result = await api.writeProgress(this.userId, { ...operation, base_version: this.version });
          if (!await this.signedIn()) return;
          this.accept(result);
          this.queue = this.queue.filter(op => op.operation_id !== operation.operation_id);
          conflicts = 0;
          await this.persist();
          this.publish();
        } catch (error) {
          if (error instanceof ApiError && (error.status === 422 || error.status === 413)) {
            await setStored(`${this.cacheKey}_rejected_change`, JSON.stringify(operation));
            this.queue = this.queue.filter(op => op.operation_id !== operation.operation_id);
            rejected = `${error.message} That change was not saved.`;
            await this.persist();
            this.publish();
            continue;
          }
          if (!(error instanceof ApiError) || error.status !== 409 || ++conflicts > 3) throw error;
          const fresh = await api.getProgress(this.userId);
          if (!await this.signedIn()) return;
          if (fresh.version === this.version) {
            if (operation.kind !== "follow") throw error;
            this.queue = this.queue.filter(op => op.operation_id !== operation.operation_id);
            rejected = "A plan was removed on another device. Add it again to follow it.";
            await this.persist();
            this.publish();
            continue;
          }
          this.accept(fresh);
          this.publish();
        }
      }
      await this.persist();
      if (this.alive) this.onStatus(rejected || (this.queue.length ? "Changes waiting to sync" : "Plans saved to your account"));
    } catch (error) {
      if (this.alive) this.onStatus(error instanceof ApiError && error.status !== 401 ? `${error.message} Changes remain on this device.` : this.queue.length ? "Offline or unavailable · changes waiting to sync" : this.loadedServer ? "Showing saved plans · account sync unavailable" : "Showing this device's plans · account sync unavailable");
    } finally { this.running = false; }
  }
}

export function useAccountProgress(userId: number, username: string) {
  const [state, setState] = useState<ProgressState | null>(null);
  const [status, setStatus] = useState("Loading account plans…");
  const sync = useRef<AccountPlanSync | null>(null);
  useEffect(() => {
    const client = new AccountPlanSync(userId, username, next => setState(previous => ({ ...next, codeforcesHandle: previous ? previous.codeforcesHandle : next.codeforcesHandle, codeforcesObserved: previous ? previous.codeforcesObserved : next.codeforcesObserved, codeforcesSyncedAt: previous ? previous.codeforcesSyncedAt : next.codeforcesSyncedAt })), setStatus);
    sync.current = client;
    void client.start();
    const refresh = () => { void client.refresh(); };
    window.addEventListener("online", refresh);
    window.addEventListener("focus", refresh);
    const timer = window.setInterval(refresh, 60000);
    return () => { client.stop(); clearInterval(timer); window.removeEventListener("online", refresh); window.removeEventListener("focus", refresh); };
  }, [userId, username]);
  return { state, setState, status, mutate: (kind: string, data: Record<string, unknown>) => sync.current?.mutate(kind, data), retry: () => { void sync.current?.refresh(); } };
}

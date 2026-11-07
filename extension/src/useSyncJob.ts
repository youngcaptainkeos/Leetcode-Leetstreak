import { useEffect, useRef, useState } from "react";
import { api, ApiError, SyncJob } from "./lib/api";
import { getStored, setStored } from "./storage";

/** The backend owns execution; closing this popup only stops status polling. */
export function useSyncJob(userId: number) {
  const [active, setActive] = useState(false);
  const [ready, setReady] = useState(false);
  const [finished, setFinished] = useState<SyncJob | null>(null);
  const [error, setError] = useState("");
  const [retryAfter, setRetryAfter] = useState(0);
  const [watch, setWatch] = useState(0);
  const starting = useRef(false);

  useEffect(() => {
    let alive = true;
    let timer: ReturnType<typeof setTimeout>;
    const seenKey = `codestreak_account_${userId}:last_sync_notice`;
    let seen = "";
    setReady(false);
    async function poll() {
      if (!alive) return;
      if (starting.current) { timer = setTimeout(poll, 1000); return; }
      try {
        const { job } = await api.latestSync(userId);
        if (!alive) return;
        if (starting.current) { timer = setTimeout(poll, 1000); return; }
        const pending = job?.state === "queued" || job?.state === "running";
        setActive(pending); setError(""); setRetryAfter(0);
        if (job && !pending && job.id !== seen) {
          seen = job.id;
          setFinished(job);
          await setStored(seenKey, seen).catch(() => undefined);
        }
        if (pending && alive) timer = setTimeout(poll, 5000);
      } catch (cause) {
        if (!alive) return;
        setError("Could not check Sync status. Any accepted server job can continue; no new sync was submitted.");
        const seconds = cause instanceof ApiError ? cause.retryAfterSeconds : 0;
        setRetryAfter(seconds);
        if (!(cause instanceof ApiError && cause.status === 401)) timer = setTimeout(poll, Math.max(15, seconds) * 1000);
      } finally { if (alive) setReady(true); }
    }
    void getStored(seenKey).then(value => { seen = value || ""; }).catch(() => undefined).then(poll);
    return () => { alive = false; clearTimeout(timer); };
  }, [userId, watch]);

  async function start() {
    if (starting.current || active || !ready) return;
    starting.current = true;
    setActive(true); setError(""); setRetryAfter(0);
    try {
      const result = await api.startSync(userId);
      setWatch(value => value + 1);
      return result.job;
    } catch (cause) {
      setActive(false);
      // An interrupted response does not prove the POST failed to enqueue.
      // Read status once more rather than automatically resubmitting it.
      setWatch(value => value + 1);
      throw cause;
    } finally { starting.current = false; }
  }

  return { active, ready, finished, error, retryAfter, start };
}

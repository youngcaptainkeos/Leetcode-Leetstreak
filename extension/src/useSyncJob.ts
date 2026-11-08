import { useEffect, useRef, useState } from "react";
import { api, ApiError, SyncJob } from "./lib/api";
import { getStored, setStored } from "./storage";

/** The backend owns execution; closing this popup only stops status polling. */
export function useSyncJob(userId: number) {
  const [active, setActive] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const knownPending = useRef(false);
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
    async function poll() {
      if (!alive) return;
      if (starting.current) { timer = setTimeout(poll, 1000); return; }
      try {
        const { job } = await api.latestSync(userId);
        if (!alive) return;
        if (starting.current) { timer = setTimeout(poll, 1000); return; }
        const pending = job?.state === "queued" || job?.state === "running";
        knownPending.current = pending;
        setActive(pending); setError(""); setRetryAfter(0);
        if (job && !pending && job.id !== seen) {
          seen = job.id;
          setFinished(job);
          await setStored(seenKey, seen).catch(() => undefined);
        }
        if (pending && alive) timer = setTimeout(poll, 2000);
      } catch (cause) {
        if (!alive) return;
        // A failed optional status read is not a failed sync. Cold starts must
        // not put a global error banner on an otherwise usable dashboard.
        if (knownPending.current) setError("Sync is still running or reconnecting. Checking again shortly…");
        const seconds = cause instanceof ApiError ? cause.retryAfterSeconds : 0;
        setRetryAfter(seconds);
        if (!(cause instanceof ApiError && cause.status === 401)) timer = setTimeout(poll, Math.max(15, seconds) * 1000);
      }
    }
    void getStored(seenKey).then(value => { seen = value || ""; }).catch(() => undefined).then(poll);
    return () => { alive = false; clearTimeout(timer); };
  }, [userId, watch]);

  async function start() {
    if (starting.current || active) return;
    starting.current = true;
    setSubmitting(true); setError(""); setRetryAfter(0);
    try {
      const result = await api.startSync(userId);
      knownPending.current = result.job.state === "queued" || result.job.state === "running";
      setActive(knownPending.current);
      setWatch(value => value + 1);
      return result.job;
    } catch (cause) {
      setActive(false);
      // An interrupted response does not prove the POST failed to enqueue.
      // Read status once more rather than automatically resubmitting it.
      setWatch(value => value + 1);
      throw cause;
    } finally { starting.current = false; setSubmitting(false); }
  }

  return { active, ready: true, submitting, finished, error, retryAfter, start };
}

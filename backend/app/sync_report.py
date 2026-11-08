"""Internal platform results; no browser credentials or provider diagnostics."""
from dataclasses import dataclass


@dataclass
class SyncReport:
    leetcode: str = "pending"
    codeforces: str = "not_linked"

    @property
    def any_success(self):
        return self.leetcode == "synced" or self.codeforces in {"synced", "recent"}

    @property
    def message(self):
        problems = []
        for name, state in (("LeetCode", self.leetcode), ("Codeforces", self.codeforces)):
            if state == "unavailable":
                problems.append(f"{name} is temporarily unavailable; its saved data is unchanged.")
            elif state == "running":
                problems.append(f"{name} is already syncing in the background.")
        if not problems:
            return None
        done = [name for name, state in (("LeetCode", self.leetcode), ("Codeforces", self.codeforces))
                if state in {"synced", "recent"}]
        return ((" and ".join(done) + " synced. ") if done else "") + " ".join(problems)

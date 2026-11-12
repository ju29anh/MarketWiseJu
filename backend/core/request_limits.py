"""Small, bounded rate limiter for a single-process public demo."""
from collections import deque
from threading import Lock
from time import monotonic


class RequestLimiter:
    def __init__(self):
        self.lock = Lock()
        self.clients = {}

    def allow(self, identity, limit, window):
        now = monotonic()
        with self.lock:
            self.clients = {key: entries for key, entries in self.clients.items() if entries and now-entries[-1] < window}
            if identity not in self.clients:
                if len(self.clients) >= 1024:
                    return False, window
                self.clients[identity] = deque()
            entries = self.clients[identity]
            while entries and now-entries[0] >= window:
                entries.popleft()
            if len(entries) >= limit:
                return False, max(1, int(window-(now-entries[0]))+1)
            entries.append(now)
            return True, 0

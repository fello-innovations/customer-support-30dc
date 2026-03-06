import threading
import time
from typing import Optional


class SessionStore:
    """In-memory session store with TTL. Swap for Redis in production."""

    def __init__(self, ttl_seconds: int = 3600):
        self._store: dict[str, tuple[str, float]] = {}  # session_id -> (response_id, expires_at)
        self._ttl = ttl_seconds
        self._lock = threading.Lock()
        self._start_cleanup_thread()

    def get_previous_response_id(self, session_id: str) -> Optional[str]:
        with self._lock:
            entry = self._store.get(session_id)
            if entry is None:
                return None
            response_id, expires_at = entry
            if time.time() > expires_at:
                del self._store[session_id]
                return None
            return response_id

    def set_previous_response_id(self, session_id: str, response_id: str) -> None:
        with self._lock:
            self._store[session_id] = (response_id, time.time() + self._ttl)

    def clear_session(self, session_id: str) -> bool:
        with self._lock:
            if session_id in self._store:
                del self._store[session_id]
                return True
            return False

    def _cleanup_expired(self) -> None:
        now = time.time()
        with self._lock:
            expired = [k for k, (_, exp) in self._store.items() if now > exp]
            for key in expired:
                del self._store[key]

    def _start_cleanup_thread(self) -> None:
        def run():
            while True:
                time.sleep(300)  # every 5 minutes
                self._cleanup_expired()

        t = threading.Thread(target=run, daemon=True)
        t.start()


# Module-level singleton — initialized in app lifespan with correct TTL
_store: Optional[SessionStore] = None


def init_session_store(ttl_seconds: int) -> None:
    global _store
    _store = SessionStore(ttl_seconds=ttl_seconds)


def get_session_store() -> SessionStore:
    if _store is None:
        raise RuntimeError("Session store not initialized")
    return _store

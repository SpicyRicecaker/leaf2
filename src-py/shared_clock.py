import threading
import time

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

FRAME_MS     = 16.67
START_FRAME  = 0
START_PAUSED = False

# ---------------------------------------------------------------------------

class SharedClock:

    FRAME_DURATION = FRAME_MS / 1000.0

    def __init__(self):
        self._lock   = threading.Lock()
        self._paused = START_PAUSED
        self._offset = START_FRAME * self.FRAME_DURATION
        self._base   = time.perf_counter()

    # ------------------------------------------------------------------

    def get_time(self) -> float:
        with self._lock:
            return self._read_locked()

    def set_time(self, t: float):
        with self._lock:
            self._offset = max(0.0, t)
            self._base   = time.perf_counter()

    def get_frame(self) -> int:
        return int(self.get_time() / self.FRAME_DURATION)

    def set_frame(self, frame: int):
        self.set_time(max(0, frame) * self.FRAME_DURATION)

    def step_frames(self, delta: int):
        with self._lock:
            current      = self._read_locked()
            frame        = int(current / self.FRAME_DURATION) + delta
            frame        = max(0, frame)
            self._paused = True
            self._offset = frame * self.FRAME_DURATION
            self._base   = time.perf_counter()

    def pause(self):
        with self._lock:
            if not self._paused:
                self._offset = self._read_locked()
                self._base   = time.perf_counter()
                self._paused = True

    def resume(self):
        with self._lock:
            if self._paused:
                self._base   = time.perf_counter()
                self._paused = False

    def toggle_pause(self):
        with self._lock:
            if self._paused:
                self._base   = time.perf_counter()
                self._paused = False
            else:
                self._offset = self._read_locked()
                self._base   = time.perf_counter()
                self._paused = True

    def reset(self):
        with self._lock:
            self._offset = START_FRAME * self.FRAME_DURATION
            self._base   = time.perf_counter()
            self._paused = START_PAUSED

    def is_paused(self) -> bool:
        with self._lock:
            return self._paused

    # ------------------------------------------------------------------

    def _read_locked(self) -> float:
        if self._paused:
            return self._offset
        return self._offset + (time.perf_counter() - self._base)
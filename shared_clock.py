import threading
import time

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

FRAME_MS    = 16.67          # milliseconds per frame  (~60 fps)
START_FRAME = 0              # which frame to begin on
START_PAUSED = False         # if True, scene starts frozen

# ---------------------------------------------------------------------------

class SharedClock:
    """
    Thread-safe clock that supports pause, resume, and direct time-seeking.

    All times are in seconds internally.
    """

    FRAME_DURATION = FRAME_MS / 1000.0   # seconds per frame

    def __init__(self):
        self._lock        = threading.Lock()
        self._paused      = START_PAUSED
        self._offset      = START_FRAME * self.FRAME_DURATION  # logical time
        self._base        = time.perf_counter()                 # wall-clock anchor

    # ------------------------------------------------------------------
    # Public API (all thread-safe)
    # ------------------------------------------------------------------

    def get_time(self) -> float:
        """Return current logical elapsed time in seconds."""
        with self._lock:
            return self._read_locked()

    def set_time(self, t: float):
        """
        Jump to an arbitrary logical time t (seconds).
        Re-anchors the wall-clock base so playback continues from here.
        """
        with self._lock:
            self._offset = max(0.0, t)
            self._base   = time.perf_counter()

    def get_frame(self) -> int:
        """Return the current frame index (0-based)."""
        return int(self.get_time() / self.FRAME_DURATION)

    def set_frame(self, frame: int):
        """Jump to the start of a specific frame."""
        self.set_time(max(0, frame) * self.FRAME_DURATION)

    def step_frames(self, delta: int):
        """
        Step forward (delta > 0) or backward (delta < 0) by N frames.
        Automatically pauses if not already paused.
        """
        with self._lock:
            current = self._read_locked()
            frame   = int(current / self.FRAME_DURATION) + delta
            frame   = max(0, frame)
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
                # re-anchor so time continues from _offset
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

    def is_paused(self) -> bool:
        with self._lock:
            return self._paused

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _read_locked(self) -> float:
        """Must be called with self._lock held."""
        if self._paused:
            return self._offset
        return self._offset + (time.perf_counter() - self._base)
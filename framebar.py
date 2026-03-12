import threading
import tkinter as tk
import ctypes
import ctypes.wintypes

from shared_clock import SharedClock, FRAME_MS

# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------

WIN_W          = 1280          # must match main.py WIN_W
WIN_H_BAR      = 90            # total height of the framebar window
CONTROL_H      = 28            # height of the top control strip
CANVAS_H       = WIN_H_BAR - CONTROL_H

VIEWPORT_FRAMES = 32           # how many frames are visible at once
CELL_W          = WIN_W // VIEWPORT_FRAMES   # 40 px per cell
CELL_PADDING    = 2            # px gap between cells

# Colours
COL_BG         = "#1e1e2e"
COL_PAST       = "#3a3a4a"
COL_CURRENT    = "#ff5555"
COL_FUTURE     = "#5a5a7a"
COL_TEXT       = "#ffffff"
COL_BTN_BG     = "#2a2a3e"
COL_BTN_FG     = "#ccccff"

# ---------------------------------------------------------------------------

class FrameBar:
    """
    Runs a tkinter window in a daemon thread.
    Positioned just below the main pygame window.
    """

    def __init__(self, clock: SharedClock, main_hwnd: int):
        self._clock      = clock
        self._hwnd       = main_hwnd        # HWND of the pygame window
        self._thread     = threading.Thread(target=self._run, daemon=True)

        # viewport state
        self._scroll     = 0               # index of the leftmost visible frame
        self._last_frame = -1              # for dirty checking

        # scrub state
        self._scrubbing  = False

    # ------------------------------------------------------------------

    def start(self):
        self._thread.start()

    # ------------------------------------------------------------------

    def _get_main_window_rect(self):
        """Return (left, top, right, bottom) of the pygame window."""
        rect = ctypes.wintypes.RECT()
        ctypes.windll.user32.GetWindowRect(
            ctypes.wintypes.HWND(self._hwnd),
            ctypes.byref(rect),
        )
        return rect

    # ------------------------------------------------------------------

    def _run(self):
        rect = self._get_main_window_rect()
        x    = rect.left
        y    = rect.bottom      # place bar directly below pygame window

        # ---- root window  --------------------------------------------
        self._root = tk.Tk()
        self._root.title("Frame Bar")
        self._root.configure(bg=COL_BG)
        self._root.resizable(False, False)
        self._root.geometry(f"{WIN_W}x{WIN_H_BAR}+{x}+{y}")

        # prevent tkinter from taking focus away on startup
        self._root.after(100, lambda: None)

        # ---- control row  --------------------------------------------
        ctrl = tk.Frame(self._root, bg=COL_BG, height=CONTROL_H)
        ctrl.pack(side=tk.TOP, fill=tk.X)
        ctrl.pack_propagate(False)

        self._play_btn = tk.Button(
            ctrl,
            text="⏸ Pause" if not self._clock.is_paused() else "▶ Play",
            bg=COL_BTN_BG, fg=COL_BTN_FG,
            activebackground="#3a3a5e", activeforeground=COL_TEXT,
            relief=tk.FLAT, padx=8,
            command=self._toggle_pause,
        )
        self._play_btn.pack(side=tk.LEFT, padx=(6, 4), pady=2)

        self._frame_label = tk.Label(
            ctrl,
            text="Frame: 0",
            bg=COL_BG, fg=COL_TEXT,
            font=("Consolas", 10),
        )
        self._frame_label.pack(side=tk.LEFT, padx=10)

        # ---- canvas  -------------------------------------------------
        self._canvas = tk.Canvas(
            self._root,
            width=WIN_W, height=CANVAS_H,
            bg=COL_BG, highlightthickness=0,
        )
        self._canvas.pack(side=tk.TOP, fill=tk.X)

        # canvas mouse bindings
        self._canvas.bind("<ButtonPress-1>",   self._on_press)
        self._canvas.bind("<B1-Motion>",        self._on_drag)
        self._canvas.bind("<ButtonRelease-1>", self._on_release)

        # keyboard bindings (framebar window focused)
        self._root.bind("<space>",  lambda e: self._toggle_pause())
        self._root.bind("<Right>",  lambda e: self._step(1))
        self._root.bind("<Left>",   lambda e: self._step(-1))

        # ---- start polling loop  ------------------------------------
        self._poll()
        self._root.mainloop()

    # ------------------------------------------------------------------
    # Polling / drawing
    # ------------------------------------------------------------------

    def _poll(self):
        frame = self._clock.get_frame()

        # --- auto-scroll: keep playhead at centre when near right edge --
        viewport_end = self._scroll + VIEWPORT_FRAMES - 1
        centre       = self._scroll + VIEWPORT_FRAMES // 2

        if frame >= viewport_end:
            self._scroll = max(0, frame - VIEWPORT_FRAMES // 2)

        # dirty check — only redraw when frame changes
        if frame != self._last_frame:
            self._last_frame = frame
            self._draw(frame)

            # update label
            self._frame_label.config(text=f"Frame: {frame}")

            # update play/pause button text
            self._play_btn.config(
                text="▶ Play" if self._clock.is_paused() else "⏸ Pause"
            )

        self._root.after(33, self._poll)

    # ------------------------------------------------------------------

    def _draw(self, current_frame: int):
        c = self._canvas
        c.delete("all")

        for i in range(VIEWPORT_FRAMES):
            frame_idx = self._scroll + i

            # colour based on relation to playhead
            if frame_idx < current_frame:
                fill = COL_PAST
            elif frame_idx == current_frame:
                fill = COL_CURRENT
            else:
                fill = COL_FUTURE

            x0 = i * CELL_W + CELL_PADDING
            y0 = CELL_PADDING
            x1 = (i + 1) * CELL_W - CELL_PADDING
            y1 = CANVAS_H - CELL_PADDING

            c.create_rectangle(x0, y0, x1, y1, fill=fill, outline="")

            # frame number inside each cell (every 4th frame to avoid clutter)
            if frame_idx % 4 == 0:
                c.create_text(
                    (x0 + x1) // 2, (y0 + y1) // 2,
                    text=str(frame_idx),
                    fill=COL_TEXT,
                    font=("Consolas", 8),
                )

    # ------------------------------------------------------------------
    # Mouse handlers
    # ------------------------------------------------------------------

    def _canvas_x_to_frame(self, canvas_x: int) -> int:
        cell  = max(0, min(VIEWPORT_FRAMES - 1, canvas_x // CELL_W))
        return self._scroll + cell

    def _on_press(self, event):
        self._scrubbing = True
        frame = self._canvas_x_to_frame(event.x)
        self._clock.set_frame(frame)

    def _on_drag(self, event):
        if self._scrubbing:
            frame = self._canvas_x_to_frame(event.x)
            self._clock.set_frame(frame)

    def _on_release(self, event):
        self._scrubbing = False

    # ------------------------------------------------------------------
    # Controls
    # ------------------------------------------------------------------

    def _toggle_pause(self):
        self._clock.toggle_pause()
        self._play_btn.config(
            text="▶ Play" if self._clock.is_paused() else "⏸ Pause"
        )

    def _step(self, delta: int):
        self._clock.step_frames(delta)
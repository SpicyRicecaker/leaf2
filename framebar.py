import threading
import tkinter as tk
import ctypes
import ctypes.wintypes

from shared_clock import SharedClock, FRAME_MS

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

WIN_W           = 1280
CONTROL_H       = 28
CANVAS_H        = 52
SCROLLBAR_H     = 14
WIN_H_BAR       = CONTROL_H + CANVAS_H + SCROLLBAR_H

VIEWPORT_FRAMES = 32
CELL_W          = WIN_W // VIEWPORT_FRAMES
CELL_PADDING    = 2

# ---------------------------------------------------------------------------
# Behaviour
# ---------------------------------------------------------------------------

LOOKAHEAD          = 64
EDGE_ZONE          = 30
EDGE_INTERVAL_MS   = 80
EDGE_SCROLL_SPEED  = 1
SCROLL_WHEEL_SPEED = 4
MIN_THUMB_W        = 20

# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------

COL_BG          = "#1e1e2e"
COL_PAST        = "#3a3a4a"
COL_CURRENT     = "#ff5555"
COL_FUTURE      = "#5a5a7a"
COL_TEXT        = "#ffffff"
COL_TEXT_DIM    = "#888899"
COL_BTN_BG      = "#2a2a3e"
COL_BTN_FG      = "#ccccff"
COL_BTN_ACTIVE  = "#3a3a5e"
COL_TRACK       = "#2a2a3e"
COL_THUMB_IDLE  = "#6666aa"
COL_THUMB_HOVER = "#9999cc"
COL_THUMB_DRAG  = "#bbbbee"

# ---------------------------------------------------------------------------


class FrameBar:

    def __init__(self, clock: SharedClock, main_hwnd: int):
        self._clock   = clock
        self._hwnd    = main_hwnd
        self._thread  = threading.Thread(target=self._run, daemon=True)

        self._scroll       = 0
        self._last_frame   = -1

        self._total_frames = LOOKAHEAD
        self._hwm          = LOOKAHEAD

        self._scrubbing      = False
        self._edge_job       = None
        self._edge_direction = 0
        self._last_mouse_x   = 0

        self._sb_state             = "IDLE"
        self._sb_drag_start_x      = 0
        self._sb_drag_start_scroll = 0

        self._manual_scroll = False   # <-- new

    # ------------------------------------------------------------------

    def start(self):
        self._thread.start()

    # ------------------------------------------------------------------

    def _get_main_rect(self):
        rect = ctypes.wintypes.RECT()
        ctypes.windll.user32.GetWindowRect(
            ctypes.wintypes.HWND(self._hwnd),
            ctypes.byref(rect),
        )
        return rect

    # ------------------------------------------------------------------

    def _run(self):
        rect = self._get_main_rect()

        self._root = tk.Tk()
        self._root.title("Frame Bar")
        self._root.configure(bg=COL_BG)
        self._root.resizable(False, False)
        self._root.geometry(
            f"{WIN_W}x{WIN_H_BAR}+{rect.left}+{rect.bottom}"
        )

        self._build_ui()
        self._bind_keys()
        self._poll()
        self._root.mainloop()

    # ------------------------------------------------------------------

    def _build_ui(self):
        ctrl = tk.Frame(self._root, bg=COL_BG, height=CONTROL_H)
        ctrl.pack(side=tk.TOP, fill=tk.X)
        ctrl.pack_propagate(False)

        btn_cfg = dict(
            bg=COL_BTN_BG, fg=COL_BTN_FG,
            activebackground=COL_BTN_ACTIVE, activeforeground=COL_TEXT,
            relief=tk.FLAT, padx=8, pady=0,
        )

        self._play_btn = tk.Button(
            ctrl,
            text="⏸ Pause" if not self._clock.is_paused() else "▶ Play",
            command=self._toggle_pause,
            **btn_cfg,
        )
        self._play_btn.pack(side=tk.LEFT, padx=(6, 2), pady=2)

        tk.Button(
            ctrl,
            text="↺ Reset",
            command=self._reset,
            **btn_cfg,
        ).pack(side=tk.LEFT, padx=(2, 2), pady=2)

        self._frame_label = tk.Label(
            ctrl,
            text="Frame: 0",
            bg=COL_BG, fg=COL_TEXT,
            font=("Consolas", 10),
        )
        self._frame_label.pack(side=tk.LEFT, padx=10)

        self._canvas = tk.Canvas(
            self._root,
            width=WIN_W, height=CANVAS_H,
            bg=COL_BG, highlightthickness=0,
        )
        self._canvas.pack(side=tk.TOP, fill=tk.X)

        self._canvas.bind("<ButtonPress-1>",   self._cell_press)
        self._canvas.bind("<B1-Motion>",        self._cell_drag)
        self._canvas.bind("<ButtonRelease-1>", self._cell_release)
        self._canvas.bind("<MouseWheel>",       self._on_wheel)

        self._sb = tk.Canvas(
            self._root,
            width=WIN_W, height=SCROLLBAR_H,
            bg=COL_TRACK, highlightthickness=0,
        )
        self._sb.pack(side=tk.TOP, fill=tk.X)

        self._sb.bind("<ButtonPress-1>",   self._sb_press)
        self._sb.bind("<B1-Motion>",        self._sb_drag)
        self._sb.bind("<ButtonRelease-1>", self._sb_release)
        self._sb.bind("<Motion>",           self._sb_motion)
        self._sb.bind("<Leave>",            self._sb_leave)
        self._sb.bind("<MouseWheel>",       self._on_wheel)

    # ------------------------------------------------------------------

    def _bind_keys(self):
        self._root.bind("<space>", lambda e: self._toggle_pause())
        self._root.bind("<Right>", lambda e: self._step(1))
        self._root.bind("<Left>",  lambda e: self._step(-1))
        self._root.bind("r",       lambda e: self._reset())

    # ------------------------------------------------------------------

    def _poll(self):
        frame = self._clock.get_frame()

        # grow timeline
        candidate = frame + LOOKAHEAD
        if candidate > self._hwm:
            self._hwm          = candidate
            self._total_frames = self._hwm

        # auto-centre — suppressed while _manual_scroll is set      # <-- changed
        if not self._manual_scroll and self._sb_state != "DRAGGING": # <-- changed
            viewport_right = self._scroll + VIEWPORT_FRAMES - 1
            if frame >= viewport_right:
                self._scroll = max(0, frame - VIEWPORT_FRAMES // 2)
                self._clamp_scroll()

        if frame != self._last_frame:
            self._last_frame = frame
            self._draw_cells(frame)
            self._draw_scrollbar()
            self._frame_label.config(text=f"Frame: {frame}")
            self._play_btn.config(
                text="▶ Play" if self._clock.is_paused() else "⏸ Pause"
            )

        self._root.after(33, self._poll)

    # ------------------------------------------------------------------

    def _draw_cells(self, current_frame: int):
        c = self._canvas
        c.delete("all")

        for i in range(VIEWPORT_FRAMES):
            fidx = self._scroll + i

            if fidx < current_frame:
                fill = COL_PAST
            elif fidx == current_frame:
                fill = COL_CURRENT
            else:
                fill = COL_FUTURE

            x0 = i * CELL_W + CELL_PADDING
            y0 = CELL_PADDING
            x1 = (i + 1) * CELL_W - CELL_PADDING
            y1 = CANVAS_H - CELL_PADDING

            c.create_rectangle(x0, y0, x1, y1, fill=fill, outline="")

            if fidx % 4 == 0:
                c.create_text(
                    (x0 + x1) // 2, (y0 + y1) // 2,
                    text=str(fidx),
                    fill=COL_TEXT_DIM,
                    font=("Consolas", 8),
                )

    def _draw_scrollbar(self):
        c = self._sb
        c.delete("all")

        tl, tr = self._thumb_rect()

        if self._sb_state == "DRAGGING":
            colour = COL_THUMB_DRAG
        elif self._sb_state == "HOVER":
            colour = COL_THUMB_HOVER
        else:
            colour = COL_THUMB_IDLE

        c.create_rectangle(
            tl, 1, tr, SCROLLBAR_H - 1,
            fill=colour, outline="",
        )

    # ------------------------------------------------------------------

    def _thumb_rect(self) -> tuple[int, int]:
        ratio    = VIEWPORT_FRAMES / max(self._total_frames, VIEWPORT_FRAMES)
        thumb_w  = max(MIN_THUMB_W, int(ratio * WIN_W))
        max_left = WIN_W - thumb_w
        thumb_l  = int((self._scroll / max(1, self._total_frames)) * WIN_W)
        thumb_l  = max(0, min(thumb_l, max_left))
        return thumb_l, thumb_l + thumb_w

    def _scroll_from_thumb_left(self, thumb_left: int) -> int:
        ratio    = VIEWPORT_FRAMES / max(self._total_frames, VIEWPORT_FRAMES)
        thumb_w  = max(MIN_THUMB_W, int(ratio * WIN_W))
        max_left = max(1, WIN_W - thumb_w)
        frac     = max(0.0, min(1.0, thumb_left / max_left))
        return int(frac * (self._total_frames - VIEWPORT_FRAMES))

    def _clamp_scroll(self):
        max_scroll   = max(0, self._total_frames - VIEWPORT_FRAMES)
        self._scroll = max(0, min(self._scroll, max_scroll))

    # ------------------------------------------------------------------
    # Scrollbar mouse handlers
    # ------------------------------------------------------------------

    def _sb_motion(self, event):
        if self._sb_state == "DRAGGING":
            return
        tl, tr = self._thumb_rect()
        if tl <= event.x <= tr:
            if self._sb_state != "HOVER":
                self._sb_state = "HOVER"
                self._draw_scrollbar()
        else:
            if self._sb_state != "IDLE":
                self._sb_state = "IDLE"
                self._draw_scrollbar()

    def _sb_leave(self, _event):
        if self._sb_state == "HOVER":
            self._sb_state = "IDLE"
            self._draw_scrollbar()

    def _sb_press(self, event):
        self._manual_scroll = True    # <-- new

        tl, tr = self._thumb_rect()

        if tl <= event.x <= tr:
            self._sb_state             = "DRAGGING"
            self._sb_drag_start_x      = event.x
            self._sb_drag_start_scroll = self._scroll
        else:
            ratio    = VIEWPORT_FRAMES / max(self._total_frames, VIEWPORT_FRAMES)
            thumb_w  = max(MIN_THUMB_W, int(ratio * WIN_W))
            new_left = event.x - thumb_w // 2
            self._scroll = self._scroll_from_thumb_left(new_left)
            self._clamp_scroll()
            self._draw_cells(self._clock.get_frame())
            self._draw_scrollbar()

    def _sb_drag(self, event):
        if self._sb_state != "DRAGGING":
            return

        if not self._clock.is_paused():
            self._sb_state = "IDLE"
            return

        delta_x  = event.x - self._sb_drag_start_x
        ratio    = VIEWPORT_FRAMES / max(self._total_frames, VIEWPORT_FRAMES)
        thumb_w  = max(MIN_THUMB_W, int(ratio * WIN_W))
        max_left = max(1, WIN_W - thumb_w)
        new_left = int(
            (self._sb_drag_start_scroll / max(1, self._total_frames)) * WIN_W
        ) + delta_x
        self._scroll = self._scroll_from_thumb_left(new_left)
        self._clamp_scroll()
        self._draw_cells(self._clock.get_frame())
        self._draw_scrollbar()

    def _sb_release(self, event):
        if self._sb_state == "DRAGGING":
            self._sb_state = "IDLE"
            self._draw_scrollbar()
        # note: _manual_scroll intentionally stays True until play  # <-- new

    # ------------------------------------------------------------------
    # Frame-canvas mouse handlers
    # ------------------------------------------------------------------

    def _canvas_x_to_frame(self, x: int) -> int:
        cell = max(0, min(VIEWPORT_FRAMES - 1, x // CELL_W))
        return self._scroll + cell

    def _cell_press(self, event):
        self._scrubbing    = True
        self._last_mouse_x = event.x
        frame = self._canvas_x_to_frame(event.x)
        self._clock.set_frame(frame)

    def _cell_drag(self, event):
        if not self._scrubbing:
            return

        self._last_mouse_x = event.x
        frame = self._canvas_x_to_frame(event.x)
        self._clock.set_frame(frame)

        if event.x < EDGE_ZONE:
            self._start_edge_scroll(-1)
        elif event.x > WIN_W - EDGE_ZONE:
            self._start_edge_scroll(1)
        else:
            self._cancel_edge_scroll()

    def _cell_release(self, _event):
        self._scrubbing = False
        self._cancel_edge_scroll()

    # ------------------------------------------------------------------
    # Edge-scroll
    # ------------------------------------------------------------------

    def _start_edge_scroll(self, direction: int):
        if self._edge_direction == direction and self._edge_job is not None:
            return
        self._cancel_edge_scroll()
        self._edge_direction = direction
        self._edge_tick()

    def _cancel_edge_scroll(self):
        if self._edge_job is not None:
            self._root.after_cancel(self._edge_job)
            self._edge_job       = None
            self._edge_direction = 0

    def _edge_tick(self):
        if not self._scrubbing:
            self._cancel_edge_scroll()
            return

        self._scroll += self._edge_direction * EDGE_SCROLL_SPEED
        self._clamp_scroll()

        frame = self._canvas_x_to_frame(self._last_mouse_x)
        self._clock.set_frame(frame)

        self._draw_cells(self._clock.get_frame())
        self._draw_scrollbar()

        self._edge_job = self._root.after(EDGE_INTERVAL_MS, self._edge_tick)

    # ------------------------------------------------------------------
    # Mouse wheel
    # ------------------------------------------------------------------

    def _on_wheel(self, event):
        self._manual_scroll = True                                # <-- new
        direction     = -1 if event.delta > 0 else 1
        self._scroll += direction * SCROLL_WHEEL_SPEED
        self._clamp_scroll()
        self._draw_cells(self._clock.get_frame())
        self._draw_scrollbar()

    # ------------------------------------------------------------------
    # Controls
    # ------------------------------------------------------------------

    def _toggle_pause(self):
        self._clock.toggle_pause()
        # resuming playback hands scroll control back to auto-centre  # <-- new
        if not self._clock.is_paused():                               # <-- new
            self._manual_scroll = False                               # <-- new
        self._play_btn.config(
            text="▶ Play" if self._clock.is_paused() else "⏸ Pause"
        )

    def _step(self, delta: int):
        self._clock.step_frames(delta)

    def _reset(self):
        self._clock.reset()
        self._scroll        = 0
        self._hwm           = LOOKAHEAD
        self._total_frames  = LOOKAHEAD
        self._manual_scroll = False    # <-- new
        self._draw_cells(0)
        self._draw_scrollbar()
        self._frame_label.config(text="Frame: 0")
        self._play_btn.config(
            text="▶ Play" if self._clock.is_paused() else "⏸ Pause"
        )
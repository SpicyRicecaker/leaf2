import threading
import time
import math

import matplotlib
matplotlib.use("TkAgg")          # explicit backend before importing pyplot
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np


class RealtimeGraph:
    """
    Spawns a separate thread that owns a matplotlib window.
    The dot position is driven by  y = x,  where x oscillates 0→1→0
    in sync with the main program's time.
    """

    def __init__(self, get_time_fn):
        """
        get_time_fn : callable that returns elapsed seconds (float).
                      Passed in so the graph stays in sync with the
                      OpenGL scene's clock.
        """
        self._get_time = get_time_fn
        self._running  = False
        self._thread   = threading.Thread(target=self._run, daemon=True)

    # ------------------------------------------------------------------
    def start(self):
        self._running = True
        self._thread.start()

    def stop(self):
        self._running = False

    # ------------------------------------------------------------------
    def _compute_x(self) -> float:
        """
        Map elapsed time to x in [0, 1].
        Uses a 4-second period triangle wave so the dot slides
        smoothly back and forth along  y = x.
        """
        t      = self._get_time()
        period = 4.0
        phase  = (t % period) / period   # 0 … 1
        # triangle wave: 0→1 then 1→0
        if phase < 0.5:
            return phase * 2.0
        else:
            return (1.0 - phase) * 2.0

    # ------------------------------------------------------------------
    def _run(self):
        # ---- static line  y = x  -------------------------------------
        line_x = np.linspace(0.0, 1.0, 200)
        line_y = line_x.copy()

        # ---- figure setup  -------------------------------------------
        fig, ax = plt.subplots(figsize=(5, 5))
        fig.patch.set_facecolor("#1e1e2e")
        ax.set_facecolor("#1e1e2e")

        ax.set_xlim(0.0, 1.0)
        ax.set_ylim(0.0, 1.0)
        ax.set_aspect("equal")

        ax.set_xlabel("x", color="white")
        ax.set_ylabel("y", color="white")
        ax.set_title("y = x  (real-time)", color="white", pad=10)

        ax.tick_params(colors="white")
        for spine in ax.spines.values():
            spine.set_edgecolor("#555577")

        ax.grid(True, color="#333355", linestyle="--", linewidth=0.6)

        # static line
        ax.plot(line_x, line_y,
                color="#88aaff", linewidth=1.8,
                label="y = x", zorder=2)

        # moving dot  (single-element scatter so we can update offsets)
        scatter = ax.scatter([0.0], [0.0],
                             s=90,
                             color="#ff5555",
                             zorder=5,
                             label="current point")

        # coordinate text next to the dot
        coord_text = ax.text(0.02, 0.02, "",
                             color="white",
                             fontsize=9,
                             transform=ax.transAxes)

        ax.legend(facecolor="#2a2a3e", edgecolor="#555577",
                  labelcolor="white", fontsize=9,
                  loc="upper left")

        # ---- animation callback  -------------------------------------
        def update(_frame):
            if not self._running:
                plt.close(fig)
                return scatter, coord_text

            x = self._compute_x()
            y = x                          # y = x

            scatter.set_offsets([[x, y]])

            coord_text.set_text(f"({x:.3f},  {y:.3f})")

            return scatter, coord_text

        ani = animation.FuncAnimation(
            fig,
            update,
            interval=33,          # ~30 fps refresh
            blit=True,
            cache_frame_data=False,
        )

        plt.tight_layout()
        plt.show()                 # blocks until the window is closed
        self._running = False      # signal main loop if user closed graph
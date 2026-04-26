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

    def __init__(self, get_time_fn, predictor):
        """
        get_time_fn : callable that returns elapsed seconds (float).
                      Passed in so the graph stays in sync with the
                      OpenGL scene's clock.
        """
        self._get_time = get_time_fn
        self._running  = False
        self._thread   = threading.Thread(target=self._run, daemon=True)
        self.predictor = predictor

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
        return t
        # period = 4.0
        # phase  = (t % period) / period   # 0 … 1
        # # triangle wave: 0→1 then 1→0
        # if phase < 0.5:
        #     return phase * 2.0
        # else:
        #     return (1.0 - phase) * 2.0

    def _run(self):
        # ---- figure setup  -------------------------------------------
        fig, ax = plt.subplots(figsize=(5, 5))
        fig.patch.set_facecolor("#1e1e2e")
        ax.set_facecolor("#1e1e2e")

        ax.set_xlabel("t", color="white")
        ax.set_ylabel("value", color="white")
        ax.set_title("ux / uz / omy  vs  t  (real-time)", color="white", pad=10)

        ax.tick_params(colors="white")
        for spine in ax.spines.values():
            spine.set_edgecolor("#555577")

        ax.grid(True, color="#333355", linestyle="--", linewidth=0.6)

        # ---- static lines for each variable  -------------------------
        t_data  = self.predictor.df.t.values
        ux_data = self.predictor.df.ux.values
        uz_data = self.predictor.df.uz.values
        omy_data = self.predictor.df.omy.values

        ax.plot(t_data, ux_data,
                color="#88aaff", linewidth=1.8,
                label="ux", zorder=2)

        ax.plot(t_data, uz_data,
                color="#88ff88", linewidth=1.8,
                label="uz", zorder=2)

        ax.plot(t_data, omy_data,
                color="#ffaa55", linewidth=1.8,
                label="omy", zorder=2)

        # ---- moving vertical line  -----------------------------------
        t_min = t_data[0]
        t_max = t_data[-1]

        # axvline returns a Line2D we can update
        vline = ax.axvline(x=t_min,
                        color="#ff5555",
                        linewidth=1.5,
                        linestyle="--",
                        zorder=5,
                        label="current t")

        # text showing current t and the three values at that point
        coord_text = ax.text(0.02, 0.97, "",
                            color="white",
                            fontsize=9,
                            transform=ax.transAxes,
                            verticalalignment="top")

        ax.legend(facecolor="#2a2a3e", edgecolor="#555577",
                labelcolor="white", fontsize=9,
                loc="upper right")

        # ---- animation callback  -------------------------------------
        def update(_frame):
            if not self._running:
                plt.close(fig)
                return vline, coord_text

            # _compute_x() should return a value in [t_min, t_max]
            t_now = self._compute_x()

            # clamp so the line never leaves the plot
            t_now = float(np.clip(t_now, t_min, t_max))

            # move the vertical line
            vline.set_xdata([t_now, t_now])

            # interpolate each variable at the current t for the readout
            ux_now  = float(np.interp(t_now, t_data, ux_data))
            uz_now  = float(np.interp(t_now, t_data, uz_data))
            omy_now = float(np.interp(t_now, t_data, omy_data))

            coord_text.set_text(
                f"t={t_now:.3f}\n"
                f"ux={ux_now:.3f}\n"
                f"uz={uz_now:.3f}\n"
                f"omy={omy_now:.3f}"
            )

            return vline, coord_text

        ani = animation.FuncAnimation(
            fig,
            update,
            interval=33,           # ~30 fps
            blit=True,
            cache_frame_data=False,
        )

        plt.tight_layout()
        plt.show()                 # blocks until the window is closed
        self._running = False      # signal main loop if user closed graph

from data_wrangler import DiscTransformPredictor
import matplotlib.pyplot as py
import numpy as np

def __main__():
    df = DiscTransformPredictor('data_m01_G90.mat', 0).df
    print(df.columns, 0)
    # py.plot(df.t, df.ux)
    # py.show()

    # f(x) = a(x) + b(x)
    # a(x) =
    from scipy.fft import fft, fftfreq
    import numpy as np
    # Number of sample points
    N = 600
    # sample spacing
    T = 1.0 / 800.0
    x = np.linspace(0.0, N*T, N, endpoint=False)
    y = np.sin(50.0 * 2.0*np.pi*x) + 0.5*np.sin(80.0 * 2.0*np.pi*x)
    yf = fft(y)
    xf = fftfreq(N, T)[:N//2]
    import matplotlib.pyplot as plt
    plt.plot(xf, 2.0/N * np.abs(yf[0:N//2]))
    plt.grid()
    plt.show()

__main__()

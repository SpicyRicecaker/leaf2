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

    n = 100
    sinfreqxd = []
    cosfreqxd = []
    # .5, 1, 1.5, 2
    # over range T
    T = df.t[len(df.t) - 1] - df.t[0]
    
    for i in range(n):
        factor = (i / 2) * ((2 * np.pi) / T)
        sin_sum = 0
        cos_sum = 0
        for j in range(len(df.t) - 1):
            dx = df.t[j + 1] - df.t[j]
            x  = df.t[j]
            sin_sum += np.sin(x * factor) * df.ux[j] * dx
            cos_sum += np.cos(x * factor) * df.ux[j] * dx
        sinfreqxd.append(sin_sum * (2 / T))
        cosfreqxd.append(cos_sum * (2 / T))

    print(sinfreqxd)
    print(cosfreqxd)

__main__()

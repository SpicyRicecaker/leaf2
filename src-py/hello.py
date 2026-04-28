from data_wrangler import DiscTransformPredictor
import matplotlib.pyplot as py
import numpy as np

def f(x):
    return np.sin(x)

def __main__():
    df = DiscTransformPredictor('data_m01_G90.mat', 0).df
    print(df.columns, 0)
    # py.plot(df.t, df.ux)
    # py.show()

    # f(x) = a(x) + b(x)
    # a(x) =

    n = 5
    sinfreqxd = [0, 0, 0, 0, 0]
    freq = [0.5, 1, 1.5, 2]

    # .5, 1, 1.5, 2
    # over range T
    T = 2 * np.pi
    steps = 10
    dx = T / steps
    for i in range(n):
        factor = (i / 2) * ((2 * np.pi) / T)
        cumsum = 0
        for j in range(steps):
            x = (j * dx)
            cumsum += np.sin(x * factor) * f(x) * dx
        cumsum *= (2 / T)
        sinfreqxd[i] = cumsum

    print(sinfreqxd)
        
    # sin(x / (2pi * T))

    

    
    return

__main__()

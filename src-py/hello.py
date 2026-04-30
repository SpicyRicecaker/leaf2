from data_wrangler import DiscTransformPredictor
import matplotlib.pyplot as plt
import numpy as np
import finufft

def __main__():
    df = DiscTransformPredictor('data_m01_G90.mat', 0).df
    # print(df.columns, 0)
    
    # number of nonuniform points
    N = len(df.t)
    
    # the nonuniform points
    # x = 2 * np.pi * np.random.uniform(size=M)
    T = df.t[N-1] - df.t[0]
    
    x = df.t
    
    # their complex strengths
    # c = (np.random.standard_normal(size=M)
    # + 1J * np.random.standard_normal(size=M))
    
    plt.plot(df.t, df.ux)
    
    c = df.ux
    
    # desired number of Fourier modes (uniform outputs)
    N = 1200
    
    # calculate the transform
    f = finufft.nufft1d1(x, c, (N, ))
    print(f)
    
    # a = np.arange(- N // 2, (N // 2 - 1) + 1, 1)
    # print(a)

    # plt.plot(a, f)
    # plt.show()
    plt.plot(np.linspace(0, N // 2 / (2 * np.pi) * T, N // 2), f[N // 2:])
    plt.show()
    

__main__()

from data_wrangler import DiscTransformPredictor
import matplotlib.pyplot as plt
import numpy as np
import finufft

def __main__():
    df = DiscTransformPredictor('data_m01_G90.mat', 0).df
    # print(df.columns, 0)
    
    # number of nonuniform points
    N = len(df.t)

    ts = np.array([df.t[i] for i in range(N)])
    uxs = np.array([df.ux[i] + 0J for i in range(N)])
    
    
    # the nonuniform points
    # x = 2 * np.pi * np.random.uniform(size=M)
    df = None
    
    T = ts[N-1] - uxs[0]
    
    x = ts
    
    # their complex strengths
    # c = (np.random.standard_normal(size=M)
    # + 1J * np.random.standard_normal(size=M))
    
    #plt.plot(df.t, df.ux)
    #plt.show()
    
    c = uxs
    
    # # desired number of Fourier modes (uniform outputs)
    N = 200
    
    # # calculate the transform
    f = finufft.nufft1d1(x, c, (N, ))
    # print(f)
    
    # # a = np.arange(- N // 2, (N // 2 - 1) + 1, 1)
    # # print(a)

    # plt.plot(a, f)
    # plt.show()
    plt.plot(np.linspace(0, N // 2 / (2 * np.pi) * T, N // 2), f[N // 2:])
    plt.show()
    

__main__()

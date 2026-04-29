from data_wrangler import DiscTransformPredictor
import matplotlib.pyplot as plt
import numpy as np
import finufft

def __main__():
    df = DiscTransformPredictor('data_m01_G90.mat', 0).df
    print(df.columns, 0)
    
    # number of nonuniform points
    N = 1200
    
    # the nonuniform points
    # x = 2 * np.pi * np.random.uniform(size=M)
    T = 1
    
    x = np.linspace(0, T, N)
    
    # their complex strengths
    # c = (np.random.standard_normal(size=M)
    # + 1J * np.random.standard_normal(size=M))
    c = np.sin(50 * x * 2 * np.pi / T) + np.cos(50 * x * 2 * np.pi / T) * 0J + 0.5 * np.sin(80 * x * 2 * np.pi) + 0.5 * np.cos(80 * x * 2 * np.pi) * 0J
    
    # desired number of Fourier modes (uniform outputs)
    N = 1200
    
    # calculate the transform
    f = finufft.nufft1d1(x, c, (N, ))
    print(f)
    
    # a = np.arange(- N // 2, (N // 2 - 1) + 1, 1)
    # print(a)

    # plt.plot(a, f)
    # plt.show()
    plt.plot(np.linspace(0, N // 2 / (2 * np.pi), N // 2), f[N // 2:])
    plt.show()
    

__main__()

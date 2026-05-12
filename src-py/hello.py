from data_wrangler import DiscTransformPredictor
import matplotlib.pyplot as plt
import numpy as np
import finufft
import math


def method2(dp):

    df = dp.df
    N = 10000
    # domain = [df.t[0], df.t[len(df.t)-1]]
    domain = [3.1674, 18.7954]
    ts = np.linspace(domain[0], domain[1], N)
    print(ts)
    uxs = np.array([dp.column_at_t(ts[i], "ux") + 0j for i in range(N)])
    # uxs = 0.5 * np.sin(ts) + 0.5 * np.cos(ts)

    sp = np.fft.fft(uxs)
    d = (domain[1] - domain[0]) / N
    print(d)

    freq = np.fft.fftfreq(len(uxs), d)

    # plt.plot(ts, uxs)
    # plt.plot(ts, 0.5 * np.sin(0.4 * 2 * np.pi * ts) + 0.5 * np.sin(1.16 * 2 * np.pi * ts))
    # 0.36 1.16
    # 0.185
    # -0.5
    # peak of 0.5c+0.5s is around 0.669
    # phase shift is around
    # 0.013? 0.005?
    # 0.005
    _ = plt.plot(freq, 2 * sp.real / N, freq, 2 * sp.imag / N)
    plt.show()
    plt.plot(ts, uxs)

    X = [1 + 0.070j, 0.1 - 0.0175j]
    f = [0.382, 1.154]

    amplitudes = [np.sqrt(X[i] * X[i].conjugate()) for i in range(len(X))]
    angles = [np.atan2(X[i].imag, X[i].real) for i in range(len(X))]
    plt.plot(
        ts,
        amplitudes[0] * np.cos(f[0] * 2 * np.pi * (ts - domain[0]) + angles[0])
        + amplitudes[1] * np.cos(f[1] * 2 * np.pi * (ts - domain[0]) + angles[1]),
    )
    plt.show()


def method1(dp):
    df = dp.df
    # number of nonuniform points
    N = len(df.t)

    ts = np.array([df.t[i] for i in range(N)])
    uxs = np.array([df.ux[i] + 0j for i in range(N)])

    # the nonuniform points
    # x = 2 * np.pi * np.random.uniform(size=M)
    df = None

    T = ts[N - 1] - ts[0]

    x = ts

    # their complex strengths
    # c = (np.random.standard_normal(size=M)
    # + 1J * np.random.standard_normal(size=M))

    # plt.plot(df.t, df.ux)
    # plt.show()

    c = uxs

    # # desired number of Fourier modes (uniform outputs)
    N = 200

    # # calculate the transform
    f = finufft.nufft1d1(x, c, (N,))
    # print(f)

    # # a = np.arange(- N // 2, (N // 2 - 1) + 1, 1)
    # # print(a)

    # plt.plot(a, f)
    # plt.show()
    plt.plot(np.linspace(0, N // 2 / (2 * np.pi) * T, N // 2), f[N // 2 :])

    # plt.plot(ts, uxs)
    # plt.plot(ts, np.sin(2 * 2 * np.pi * ts))

    plt.show()


def __main__():
    dp = DiscTransformPredictor("data_m01_G90.mat", 0)
    # print(df.columns, 0)
    method2(dp)


__main__()

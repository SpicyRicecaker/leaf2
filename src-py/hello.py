from data_wrangler import DiscTransformPredictor
import matplotlib.pyplot as plt
import numpy as np
import finufft
import math


def method2(dp):
    df = dp.df
    N = 10000
    # domain = [df.t[0], df.t[len(df.t)-1]]
    domain = [14.2, 79.9]
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
    real = 2 * sp.real / N
    imag = 2 * sp.imag / N
    _ = plt.plot(freq, real, freq, imag)
    plt.show()

    amp_nonzero = 0.01
    freq_nonzero = 0.01
    X = []
    f = []
    for i in range(len(freq)):
        if freq[i] >= 0 and real[i] > amp_nonzero:
            double_counting = 1 if freq[i] >= freq_nonzero else 1 / 2
            X.append((real[i] + imag[i] * 1J) * double_counting)
            f.append(freq[i])
    f = np.array(f)
    plt.plot(ts, uxs, label="dataset")
    print(f'f {f}')


    amplitudes = np.array([np.sqrt(X[i] * X[i].conjugate()) for i in range(len(X))])
    print(f'amplitudes {amplitudes}')
    angles = np.array([np.atan2(X[i].imag, X[i].real) for i in range(len(X))])
    plt.plot(
        ts,
        sum([amplitudes[i] * np.cos(f[i] * 2 * np.pi * (ts - domain[0]) + angles[i])for i in range(len(amplitudes))]),
        label='distilled'
    )
    plt.legend()
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
    dp = DiscTransformPredictor("data_m05_G160.mat", 0)
    # print(df.columns, 0)
    method2(dp)


__main__()

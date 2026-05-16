from data_wrangler import DiscTransformPredictor
import matplotlib.pyplot as plt
import numpy as np
import finufft
import math
import pandas as pd


def read():
    df = pd.read_csv('data/data_m05_G160_fourier_transposed_ux.csv')
    print(df)
    print(complex(df['Amplitude (unit)'][0]) + 1)

def fourier_coefficients(dp, column, N=10000):
    df = dp.df
    # domain = [df.t[0], df.t[len(df.t)-1]]
    domain = [14.2, 79.9]
    ts = np.linspace(domain[0], domain[1], N)
    print(ts)
    
    uxs = np.array([dp.column_at_t(ts[i], column) + 0j for i in range(N)])
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

    data = {
      "Frequency (Hz)": f,
      "Amplitude (unit)": amplitudes,
      "Initial phase (rad)": angles
    }
    df = pd.DataFrame(data)
    key = 'ux'
    df.to_csv(f'data/{dp.path.split(".")[0]}_fourier_transposed_{key}.csv')
    #df2.to_hdf('my_data.h5', key='df2', mode='a')
    plt.legend()
    plt.show()


def __main__():
    dp = DiscTransformPredictor("data_m05_G160.mat", 0)
    # print(df.columns, 0)
    fourier_coefficients(dp, column='ux')


__main__()
import numpy as np

def FFT(x):
    """
    INPUTS:
    x (np.array): the array that must be a power of 2.

    OUTPUTS:
    the FFT of x.
    """
    N = len(x)
    
    if N == 1:
        return x # base case

    if N % 2 == 1:
        raise ("len(x) should be power of 2")

    evens = FFT(x[::2])
    odds = FFT(x[1::2]) # even and odd indices

    factor = np.exp(np.arange(N) * -2j*np.pi / N) # twiddle factors

    return np.concatenate([evens + factor[:N//2]*odds, evens + factor[N//2:]*odds])

def give_freqs(sr, signal):
    n = 2**int(np.log2(signal))
    signal = signal[:n]

    fft = abs(FFT(signal))
    freqs = np.zeros(88)
    
    for x in range(len(freqs)):
        freq = 27.5 * 2**(x/12)
        if freq > len(fft): # in case for some reason the signal has less than 88 samples
            continue
        bin = int(freq*n / sr)
        freqs[x] = np.sqrt(fft[bin]**2 + fft[bin + 1]**2)
    
    return freqs

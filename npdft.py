# NOW DEPRECATED - I USE IT FOR TESTING

# imports - self explanatory
import math
import numpy as np

# didn't use this in the end
def add_window(signal : np.array, strength : int):
    sr = len(signal)
    return np.array([signal[x]*np.clip(strength*(1-math.cos(x*math.tau/sr)), 0, 1) for x in range(sr)])

def generate_wave(freq: float, sr: int, signalLength: int, isSine: bool = True):
    x = np.arange(signalLength)
    y = x * (freq*math.tau / sr)
    if isSine:
        return np.sin(y)
    else:
        return np.cos(y)

def test(wave : np.array, signal : np.array):
    if len(wave)!=len(signal):
        raise (f"wave ({len(wave)}) and signal ({len(signal)}) do not have the same sample rate.")
    
    return np.multiply(wave,signal)

def score(sin, cos):
    return math.sqrt(sin**2 + cos**2)

# based off DFT but increases frequency geometrically
def give_freqs(sr: int, signal : np.array):
    freqs = np.zeros(88)

    for x in range(len(freqs)):
        freq = 27.5*math.pow(2, x/12)
        sin = generate_wave(freq, sr, len(signal))
        cos = generate_wave(freq, sr, len(signal), False)
        
        sintest = np.dot(sin, signal)
        costest = np.dot(cos, signal)
        freqs[x] = score(sintest, costest)

    return freqs

# for debugging
def inverse(freqs : np.array, sr : int):
    default = np.zeros(sr)
    for x in range(88):
        wave = generate_wave(27.5*math.pow(2, x/12), sr, True) * freqs[x]
        for y in range(len(default)):
            default[y] += wave[y]
    return default

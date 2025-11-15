import numpy as np
from scipy.signal import medfilt, find_peaks, correlate

def bpm_and_fastest_note(sr, signal):
    '''
    OUTPUTS:
    BPM of signal, rounded to nearest whole number
    fastest note, rounded to nearest power of 2. Measured in how many to make a crochet.
    '''

    if signal.ndim > 1:
        signal = signal.mean(axis=1)

    # make positive and smooth out
    env = np.abs(signal)
    env = medfilt(env, kernel_size=101)

    # detect onset times
    diff = np.diff(env)
    diff[diff < 0] = 0 # replace negatives with 0
    peaks, _ = find_peaks(diff, height=np.mean(diff))
    onset_times = peaks / sr

    # autocorrelation
    corr = correlate(env, env, mode="full")
    corr = corr[len(corr)//2:]

    # search for lag in range
    min_bpm = 40
    max_bpm = 240
    min_lag = int((60 / max_bpm) * sr)
    max_lag = int((60 / min_bpm) * sr)

    if max_lag >= len(corr):
        max_lag = len(corr) - 1

    lag = np.argmax(corr[min_lag:max_lag]) + min_lag
    tempo = 60 / (lag / sr)

    # too fast or too slow
    if tempo < 70:
        tempo *= 2
    elif tempo > 200:
        tempo //= 2

    # fastest note subdivision
    if len(onset_times) > 1:
        intervals = np.diff(onset_times)
        fastest_interval = np.min(intervals)
        beat_duration = 60 / tempo
        fastest_note = beat_duration / fastest_interval
        fastest_note = 2 ** round(np.log2(fastest_note))
    else:
        fastest_note = 1

    if fastest_note > 4: # faster than a semiquaver - something went wrong
        fastest_note = 4

    return int(round(tempo)), int(fastest_note)

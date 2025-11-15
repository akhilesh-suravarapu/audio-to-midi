import math

def find_key(notes_list):
    '''
    INPUTS:
    notes_list: a list of the frequency of notes from C, C#, D... to B

    OUTPUTS:
    best_key: the key that best describes the notes given
    '''

    # profiles
    major_profile = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52,
                     5.19, 2.39, 3.66, 2.29, 2.88]
    minor_profile = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54,
                     4.75, 3.98, 2.69, 3.34, 3.17]

    # normalize data 
    total = sum(notes_list)
    if total == 0:
        raise ValueError("no notes in list")
    ys = [x/total for x in notes_list]

    # Pearson correlation coefficient between a and b  
    def correlation(a, b):
        n = len(a)
        mean_a = sum(a) / n
        mean_b = sum(b) / n
        num = 0
        sum_sq_a = 0
        sum_sq_b = 0
        for i in range(n):
            da = a[i] - mean_a
            db = b[i] - mean_b
            num += da * db
            sum_sq_a += da ** 2
            sum_sq_b += db ** 2
        if sum_sq_a == 0 or sum_sq_b == 0:
            return 0  # divide by zero error: no variation
        return num / math.sqrt(sum_sq_a * sum_sq_b)

    # compute correlation of all keys by rotating them
    key_scores = []
    key_names = []

    # key names
    major_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    minor_names = ['Cm', 'C#m', 'Dm', 'D#m', 'Em', 'Fm', 'F#m', 'Gm', 'G#m', 'Am', 'A#m', 'Bm']

    for r in range(12):
        # rotate ys by r
        rotated_ys = ys[r:] + ys[:r]
        score = correlation(major_profile, rotated_ys)
        key_scores.append(score)
        key_names.append(major_names[r])

    for r in range(12):
        rotated_ys = ys[r:] + ys[:r]
        score = correlation(minor_profile, rotated_ys)
        key_scores.append(score)
        key_names.append(minor_names[r])

    # pick the key with the highest correlation coefficient
    best_index = 0
    best_value = key_scores[0]

    for x, val in enumerate(key_scores):
        if val > best_value:
            best_value = val
            best_index = x
    
    best_key = key_names[best_index]

    return best_key
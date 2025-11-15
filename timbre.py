import numpy as np

def flute(part):
    return [np.argmax(part)+21] # flute is so simple that I can just output the index+21 of the highest part

def piano(part, confidence):
    notes = []
    m = max(part)
    if m==0: # if there is no sound, return nothing
        return []
    for x in range(len(part)):
        if part[x]>=m*confidence: # all parts that are loud enough will be accepted
            notes.append((x+21,part[x]))
    return notes

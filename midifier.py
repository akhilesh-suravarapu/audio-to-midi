from midiutil import MIDIFile # to write MIDI files
import fft # discrete fourier transform
import soundfile as sf # to open waveform files
import timbre # to find the note from the frequencies
from io import BytesIO # to send to flask at the end
import keyfinder # to output key signature to app
import bpmcount # to count bpm and find suitable resolution

piano_notes = [
    'A0', 'A#0', 'B0',
    'C1', 'C#1', 'D1', 'D#1', 'E1', 'F1', 'F#1', 'G1', 'G#1', 'A1', 'A#1', 'B1',
    'C2', 'C#2', 'D2', 'D#2', 'E2', 'F2', 'F#2', 'G2', 'G#2', 'A2', 'A#2', 'B2',
    'C3', 'C#3', 'D3', 'D#3', 'E3', 'F3', 'F#3', 'G3', 'G#3', 'A3', 'A#3', 'B3',
    'C4', 'C#4', 'D4', 'D#4', 'E4', 'F4', 'F#4', 'G4', 'G#4', 'A4', 'A#4', 'B4',
    'C5', 'C#5', 'D5', 'D#5', 'E5', 'F5', 'F#5', 'G5', 'G#5', 'A5', 'A#5', 'B5',
    'C6', 'C#6', 'D6', 'D#6', 'E6', 'F6', 'F#6', 'G6', 'G#6', 'A6', 'A#6', 'B6',
    'C7', 'C#7', 'D7', 'D#7', 'E7', 'F7', 'F#7', 'G7', 'G#7', 'A7', 'A#7', 'B7',
    'C8'
] # useful for debugging

def find_notes(FILE, instrument, confidence):
    '''
    INPUTS:
    FILE - path or file in any audio format
    instrument - currently piano or flute
    confidence - the leeway given to the code: 1 will let only 1 note, 0 lets every note. 0.9 is recommended.

    OUTPUTS:
    tuple (int, str, bytes)
    seconds played, key, midi file
    '''

    # setup
    signal, sr = sf.read(FILE)

    tempo, res = bpmcount.bpm_and_fastest_note(sr, signal)

    if signal.ndim == 2:
        signal = [(l+r)//2 for l,r in signal]


    s = len(signal) / sr # total seconds of audio 
    beats = s*tempo / 60 # total beats in the signal 
    m = int(res * beats) # total measurements (frames) 
    samples = len(signal) // m # samples per measurement 

    # for debugging and other useful things
    print(f"Length of signal: {len(signal)}") 
    print(f"Sample rate: {sr}") 
    print(f"\nTempo: {tempo} BPM") 
    print(f"Resolution: 1/{res*4} note") 
    print(f"Total beats: {beats:.2f}") 
    print(f"Total measurements: {m}") 
    print(f"Samples per measurement: {samples}\n")

    # MIDIUtil stuff
    track = 0
    channel = 0
    volume = 100
    MyMIDI = MIDIFile(1)
    MyMIDI.addTempo(track, 0, tempo)
    if instrument == "flute":
        MIDIFile.addProgramChange(track, channel, 0, 74) # flute

    duration_beats = 1/res # duration of each beat

    notes_list = [[] for _ in range(m)] # this is to store each note because MIDIUtil doesn't let me edit in place
                                        # each list is one beat, and should hold note, duration and volume

    # main bit
    for i in range(m):
        part = signal[samples*i : samples*(i+1)]
        notes = fft.give_freqs(sr, part)
        if instrument == "flute":
            v = timbre.flute(notes)
        else:
            v = timbre.piano(notes, confidence)

        for note, vol in v:

            notes_list[i].append((note, duration_beats, vol)) #min beats before combining

        print(f"{round(100*(i+1)/m,1)}% (frame {i+1}/{m}) ... notes:",[piano_notes[n[0]-21] for n in v])

    if not any(x for x in notes_list): # in case there are no keys present
        raise ("no notes")

    # combine notes in-place
    print("merging...")

    for x in range(m-1, 0, -1): # iterate backwards
        b1 = notes_list[x-1]
        b2 = notes_list[x]
        if b1==[] or b2==[]:
            continue

        for note1 in b1:
            if b2==[]: #this triggers if b2 had 2+ notes that merged so it needs to loop over a blank list
                continue

            for note2 in b2:
                if note1[0] == note2[0] and note1[2] >= note2[2]*0.85:
                    newnote = (note1[0], note1[1]+note2[1], note1[2])

                    loc = notes_list[x].index(note2) 
                    del notes_list[x][loc]

                    loc = notes_list[x-1].index(note1) 
                    notes_list[x-1][loc] = newnote

    #key
    keys = [0 for _ in range(12)]
    for group in notes_list:
        for note in group:
            keys[note[0]%12] += 1 # we can nicely do mod 12 to convert them to their key bins
    key = keyfinder.find_key(keys)

    # write the thing
    for x in range(len(notes_list)):
        for note in notes_list[x]:
            MyMIDI.addNote(track, channel, note[0], x/res, note[1]/res, volume)
    
    # writes it all in storage so it doesn't consume a ton of memory every time
    midi_bytes = BytesIO()
    MyMIDI.writeFile(midi_bytes)
    midi_bytes.seek(0)
    print("done!")
    return s, key, midi_bytes

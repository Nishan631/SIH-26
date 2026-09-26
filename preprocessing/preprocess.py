import pyedflib
import numpy as np
from scipy.signal import butter, sosfiltfilt, iirnotch, filtfilt

file = "data/external/chb02_16.edf"

reader = pyedflib.EdfReader(file)

fs = 256

selected_channels = [0, 1, 2, 3, 8, 9, 10, 11]

# Seizure segment: 130 to 135 seconds
start_time = 130
duration = 5

start_sample = int(start_time * fs)
num_samples = int(duration * fs)

signals = []

for ch in selected_channels:
    signal = reader.readSignal(
        ch,
        start=start_sample,
        n=num_samples
    )
    signals.append(signal)

reader.close()

signals = np.array(signals)

print("Raw seizure segment shape:", signals.shape)


# -----------------------------
# Band-pass filter: 0.5–40 Hz
# -----------------------------

lowcut = 0.5
highcut = 40

sos = butter(
    4,
    [lowcut, highcut],
    btype="band",
    fs=fs,
    output="sos"
)

filtered_signals = sosfiltfilt(
    sos,
    signals,
    axis=1
)


# -----------------------------
# 50 Hz notch filter
# -----------------------------

notch_freq = 50
quality_factor = 30

b, a = iirnotch(
    notch_freq,
    quality_factor,
    fs
)

filtered_signals = filtfilt(
    b,
    a,
    filtered_signals,
    axis=1
)


# -----------------------------
# Save filtered EEG
# -----------------------------

np.save(
    "data/external/filtered_chb02_16.npy",
    filtered_signals
)

print("Filtered EEG saved successfully!")
print("Shape:", filtered_signals.shape)
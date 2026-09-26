from scipy.io import loadmat
from scipy.signal import butter, filtfilt, iirnotch
import numpy as np
from pathlib import Path

# --------------------------------------------------
# PATHS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]

DATA_FILE = BASE_DIR / "fatigue" / "data" / "dataset.mat"
OUTPUT_DIR = BASE_DIR / "fatigue" / "data"

# --------------------------------------------------
# LOAD DATASET
# --------------------------------------------------

print("Loading dataset...")

data = loadmat(DATA_FILE)

X = data["EEGsample"].astype(np.float64)
y = data["substate"].flatten().astype(np.uint8)
subjects = data["subindex"].flatten().astype(np.uint8)

print("Original EEG shape:", X.shape)
print("Labels shape:", y.shape)
print("Subjects shape:", subjects.shape)

# --------------------------------------------------
# SETTINGS
# --------------------------------------------------

FS = 128

# Band-pass: 0.5–40 Hz
LOWCUT = 0.5
HIGHCUT = 40.0
FILTER_ORDER = 4

# 50 Hz notch
NOTCH_FREQ = 50.0
QUALITY_FACTOR = 30.0

# --------------------------------------------------
# BAND-PASS FILTER
# --------------------------------------------------

b, a = butter(
    FILTER_ORDER,
    [LOWCUT / (FS / 2), HIGHCUT / (FS / 2)],
    btype="band"
)

# --------------------------------------------------
# NOTCH FILTER
# --------------------------------------------------

bn, an = iirnotch(
    NOTCH_FREQ,
    QUALITY_FACTOR,
    FS
)

# --------------------------------------------------
# PREPROCESS
# --------------------------------------------------

print("Preprocessing EEG...")

X_filtered = np.empty_like(X)

for i in range(X.shape[0]):

    for ch in range(X.shape[1]):

        signal = X[i, ch, :]

        # Band-pass filtering
        signal = filtfilt(b, a, signal)

        # Notch filtering
        signal = filtfilt(bn, an, signal)

        # Remove DC offset
        signal = signal - np.mean(signal)

        # Standardize each channel
        std = np.std(signal)

        if std > 1e-8:
            signal = signal / std

        X_filtered[i, ch, :] = signal

    # Progress
    if (i + 1) % 200 == 0:
        print(f"Processed {i + 1}/{X.shape[0]} samples")

# --------------------------------------------------
# SAVE OUTPUTS
# --------------------------------------------------

np.save(OUTPUT_DIR / "filtered_eeg.npy", X_filtered)
np.save(OUTPUT_DIR / "labels.npy", y)
np.save(OUTPUT_DIR / "subjects.npy", subjects)

print()
print("Preprocessing complete!")
print("Filtered EEG shape:", X_filtered.shape)

print()
print("Saved files:")
print(" - fatigue/data/filtered_eeg.npy")
print(" - fatigue/data/labels.npy")
print(" - fatigue/data/subjects.npy")
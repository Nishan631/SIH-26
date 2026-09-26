import numpy as np
from scipy.signal import welch

# Load EEG windows and labels
windows = np.load("data/windows.npy")
labels = np.load("data/labels.npy")

fs = 256

bands = {
    "delta": (0.5, 4),
    "theta": (4, 8),
    "alpha": (8, 13),
    "beta": (13, 30),
    "gamma": (30, 40)
}

all_features = []

for window in windows:

    window_features = []

    for channel in window:

        # 1. Variance
        variance = np.var(channel)

        # 2. RMS
        rms = np.sqrt(np.mean(channel ** 2))

        window_features.append(variance)
        window_features.append(rms)

        # 3. Frequency-band powers
        frequencies, power = welch(
            channel,
            fs=fs,
            nperseg=256
        )

        for low, high in bands.values():

            mask = (frequencies >= low) & (frequencies < high)

            band_power = np.trapezoid(
                power[mask],
                frequencies[mask]
            )

            window_features.append(band_power)

    all_features.append(window_features)

X = np.array(all_features)

print("Feature matrix shape:", X.shape)
print("Labels shape:", labels.shape)

# Save features
np.save("data/features.npy", X)
np.save("data/final_labels.npy", labels)

print("Features saved successfully!")
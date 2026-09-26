import numpy as np
import pyedflib
import joblib
from scipy.signal import welch
import csv

# -----------------------------
# SETTINGS
# -----------------------------

edf_file = "data/chb01_03.edf"
model_file = "models/random_forest_model_recording_split.pkl"

start_time = 2980
end_time = 3040
window_seconds = 5
fs = 256

# Same 8 channels used during training
channels = [0, 1, 2, 3, 8, 9, 10, 11]

bands = {
    "delta": (0.5, 4),
    "theta": (4, 8),
    "alpha": (8, 13),
    "beta": (13, 30),
    "gamma": (30, 40)
}

# -----------------------------
# LOAD MODEL
# -----------------------------

model = joblib.load(model_file)

# -----------------------------
# READ EEG
# -----------------------------

edf = pyedflib.EdfReader(edf_file)

signals = []

for channel in channels:
    signal = edf.readSignal(channel)
    signals.append(signal)

edf.close()

signals = np.array(signals)

# Select demo portion
start_sample = start_time * fs
end_sample = end_time * fs

signals = signals[:, start_sample:end_sample]

print("Demo EEG shape:", signals.shape)

# -----------------------------
# CREATE 5-SECOND WINDOWS
# -----------------------------

samples_per_window = window_seconds * fs

predictions = []

for start in range(0, signals.shape[1], samples_per_window):

    end = start + samples_per_window

    if end > signals.shape[1]:
        break

    window = signals[:, start:end]

    # -----------------------------
    # EXTRACT SAME 56 FEATURES
    # -----------------------------

    features = []

    for channel in window:

        variance = np.var(channel)

        rms = np.sqrt(np.mean(channel ** 2))

        features.append(variance)
        features.append(rms)

        frequencies, power = welch(
            channel,
            fs=fs,
            nperseg=256
        )

        for low, high in bands.values():

            mask = (
                (frequencies >= low)
                & (frequencies < high)
            )

            band_power = np.trapezoid(
                power[mask],
                frequencies[mask]
            )

            features.append(band_power)

    X = np.array(features).reshape(1, -1)

    # -----------------------------
    # MODEL PREDICTION
    # -----------------------------

    prediction = model.predict(X)[0]

    probability = model.predict_proba(X)[0][1]

    actual_start = start_time + start / fs
    actual_end = actual_start + window_seconds

    status = "Seizure" if prediction == 1 else "Normal"

    predictions.append([
        actual_start,
        actual_end,
        probability,
        status
    ])

    print(
        f"{actual_start:.0f}-{actual_end:.0f} sec | "
        f"{probability * 100:.2f}% | {status}"
    )

# -----------------------------
# SAVE CSV
# -----------------------------

with open(
    "data/seizure_predictions.csv",
    "w",
    newline=""
) as file:

    writer = csv.writer(file)

    writer.writerow([
        "start_time",
        "end_time",
        "seizure_probability",
        "status"
    ])

    writer.writerows(predictions)

print("\nPrediction file saved:")
print("data/seizure_predictions.csv")
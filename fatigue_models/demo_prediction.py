import numpy as np
import pandas as pd
import joblib
from scipy.signal import welch
from pathlib import Path


# --------------------------------------------------
# Paths
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[2]

DEMO_FILE = BASE_DIR / "fatigue" / "demo" / "fatigue_demo.npy"
INDICES_FILE = BASE_DIR / "fatigue" / "demo" / "fatigue_demo_indices.npy"
LABELS_FILE = BASE_DIR / "fatigue" / "demo" / "fatigue_demo_labels.npy"

MODEL_FILE = BASE_DIR / "fatigue" / "models" / "random_forest_advanced.pkl"

OUTPUT_FILE = BASE_DIR / "fatigue" / "demo" / "fatigue_predictions.csv"


# --------------------------------------------------
# Settings
# --------------------------------------------------
FS = 128

BANDS = {
    "delta": (0.5, 4),
    "theta": (4, 8),
    "alpha": (8, 13),
    "beta": (13, 30),
    "gamma": (30, 40),
}


# --------------------------------------------------
# Feature extraction
# Same 16 features/channel used during training
# --------------------------------------------------
def extract_features(epoch):
    """
    epoch shape = (30, 384)
    returns 480 features
    """

    all_features = []

    for channel in epoch:

        signal = channel.astype(np.float64)

        variance = np.var(signal)
        rms = np.sqrt(np.mean(signal ** 2))

        frequencies, power = welch(
            signal,
            fs=FS,
            nperseg=min(256, len(signal))
        )

        band_powers = {}

        for band_name, (low, high) in BANDS.items():

            mask = (frequencies >= low) & (frequencies < high)

            band_power = np.trapezoid(
                power[mask],
                frequencies[mask]
            )

            band_powers[band_name] = band_power

        total_power = sum(band_powers.values())

        if total_power > 1e-12:
            relative_powers = {
                name: value / total_power
                for name, value in band_powers.items()
            }
        else:
            relative_powers = {
                name: 0.0
                for name in band_powers
            }

        theta_alpha = (
            band_powers["theta"] /
            (band_powers["alpha"] + 1e-12)
        )

        beta_alpha = (
            band_powers["beta"] /
            (band_powers["alpha"] + 1e-12)
        )

        delta_alpha = (
            band_powers["delta"] /
            (band_powers["alpha"] + 1e-12)
        )

        theta_beta = (
            band_powers["theta"] /
            (band_powers["beta"] + 1e-12)
        )

        channel_features = [
            variance,
            rms,

            band_powers["delta"],
            band_powers["theta"],
            band_powers["alpha"],
            band_powers["beta"],
            band_powers["gamma"],

            relative_powers["delta"],
            relative_powers["theta"],
            relative_powers["alpha"],
            relative_powers["beta"],
            relative_powers["gamma"],

            theta_alpha,
            beta_alpha,
            delta_alpha,
            theta_beta,
        ]

        all_features.extend(channel_features)

    return np.array(all_features)


# --------------------------------------------------
# Load demo data
# --------------------------------------------------
print("Loading fatigue demo...")

demo_eeg = np.load(DEMO_FILE)
demo_indices = np.load(INDICES_FILE)
actual_labels = np.load(LABELS_FILE)

print("Demo EEG shape:", demo_eeg.shape)


# --------------------------------------------------
# Load trained model
# --------------------------------------------------
print("Loading trained Advanced Random Forest...")

model = joblib.load(MODEL_FILE)

print("Model loaded successfully.")


# --------------------------------------------------
# Extract features
# --------------------------------------------------
print("\nExtracting advanced features...")

features = []

for i, epoch in enumerate(demo_eeg):

    feature_vector = extract_features(epoch)

    features.append(feature_vector)

    print(
        f"Processed sample {i + 1}/{len(demo_eeg)}"
    )

features = np.array(features)

print("\nFeature shape:", features.shape)


# --------------------------------------------------
# Model prediction
# --------------------------------------------------
print("\nRunning fatigue predictions...")

predictions = model.predict(features)
probabilities = model.predict_proba(features)


# --------------------------------------------------
# Find probability of Drowsy class
# --------------------------------------------------
class_index = list(model.classes_).index(1)

drowsy_probability = probabilities[:, class_index]


# --------------------------------------------------
# Convert predictions to readable states
# --------------------------------------------------
actual_state = np.where(
    actual_labels == 1,
    "Drowsy",
    "Alert"
)

predicted_state = np.where(
    predictions == 1,
    "Drowsy",
    "Alert"
)


# --------------------------------------------------
# Confidence-aware status
# --------------------------------------------------
def get_status(probability):

    if probability >= 0.75:
        return "High Fatigue Risk"

    elif probability >= 0.50:
        return "Fatigue Detected"

    elif probability >= 0.35:
        return "Monitor"

    else:
        return "Alert / Normal"


status = [
    get_status(prob)
    for prob in drowsy_probability
]


# --------------------------------------------------
# Create timeline
# Each EEG epoch = 3 seconds
# --------------------------------------------------
start_times = np.arange(
    len(demo_eeg)
) * 3

end_times = start_times + 3


# --------------------------------------------------
# Save prediction CSV
# --------------------------------------------------
results = pd.DataFrame({
    "sample_index": demo_indices,
    "start_time": start_times,
    "end_time": end_times,
    "actual_state": actual_state,
    "predicted_state": predicted_state,
    "drowsy_probability": drowsy_probability,
    "status": status,
})


results.to_csv(
    OUTPUT_FILE,
    index=False
)


# --------------------------------------------------
# Display results
# --------------------------------------------------
print("\n----------------------------------------")
print("FATIGUE DEMO PREDICTIONS")
print("----------------------------------------")

print(results.to_string(index=False))

print("\n----------------------------------------")
print("Prediction complete!")
print("----------------------------------------")

print("Saved:")
print(OUTPUT_FILE)
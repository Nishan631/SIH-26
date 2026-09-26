import pyedflib
import numpy as np

files_and_seizures = {
    "data/chb01_03.edf": [(2996, 3036)],
    "data/chb01_04.edf": [(1467, 1494)],
    "data/chb01_15.edf": [(1732, 1772)],
    "data/chb01_16.edf": [(1015, 1066)],
    "data/chb01_18.edf": [(1720, 1810)],
    "data/chb01_21.edf": [(327, 420)],
    "data/chb01_26.edf": [(1862, 1963)]
}

selected_channels = [0, 1, 2, 3, 8, 9, 10, 11]

fs = 256
window_seconds = 5
window_samples = window_seconds * fs

all_windows = []
all_labels = []
all_recording_ids = []

for file, seizure_intervals in files_and_seizures.items():

    print("\nProcessing:", file)

    reader = pyedflib.EdfReader(file)

    total_samples = reader.getNSamples()[0]
    total_seconds = total_samples / fs

    print("Duration:", total_seconds, "seconds")

    recording_id = file.split("/")[-1].replace(".edf", "")

    for start in range(
        0,
        int(total_seconds) - window_seconds + 1,
        window_seconds
    ):

        end = start + window_seconds

        signals = []

        for ch in selected_channels:

            signal = reader.readSignal(
                ch,
                start=start * fs,
                n=window_samples
            )

            signals.append(signal)

        signals = np.array(signals)

        label = 0

        for seizure_start, seizure_end in seizure_intervals:

            if start < seizure_end and end > seizure_start:
                label = 1
                break

        all_windows.append(signals)
        all_labels.append(label)
        all_recording_ids.append(recording_id)

    reader.close()


windows = np.array(all_windows)
labels = np.array(all_labels)
recording_ids = np.array(all_recording_ids)


print("\n==============================")
print("Final Dataset")
print("==============================")

print("Windows shape:", windows.shape)
print("Labels shape:", labels.shape)
print("Recording IDs shape:", recording_ids.shape)

print("Seizure windows:", np.sum(labels == 1))
print("Non-seizure windows:", np.sum(labels == 0))

print("\nRecording distribution:")

unique_ids, counts = np.unique(recording_ids, return_counts=True)

for recording, count in zip(unique_ids, counts):
    print(recording, "->", count, "windows")


np.save("data/windows.npy", windows)
np.save("data/labels.npy", labels)
np.save("data/recording_ids.npy", recording_ids)

print("\nDataset saved successfully!")
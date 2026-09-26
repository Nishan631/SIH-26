import numpy as np
import pyedflib

input_file = "data/chb01_03.edf"
output_file = "data/demo/seizure_demo.npy"

start_time = 2980
end_time = 3040
fs = 256

channels = [0, 1, 2, 3, 8, 9, 10, 11]

edf = pyedflib.EdfReader(input_file)

signals = []

for channel in channels:
    signal = edf.readSignal(channel)

    start_sample = start_time * fs
    end_sample = end_time * fs

    signals.append(
        signal[start_sample:end_sample]
    )

edf.close()

demo_eeg = np.array(signals)

np.save(output_file, demo_eeg)

print("Demo EEG saved successfully!")
print("Shape:", demo_eeg.shape)
print("File:", output_file)
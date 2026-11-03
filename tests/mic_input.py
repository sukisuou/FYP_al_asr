# ===== input handler =====
# - receives chunks of input from device microphone
# - simulates vercel's packet PCM bytestream

import sounddevice as sd
import numpy as np
import socket

# Audio Streaming Config
SAMPLE_RATE = 16000
CHUNK_DURATION = 0.5   # Callback interval in seconds
WINDOW_DURATION = 3.0  # Sliding audio window kept for CTC context
CHUNK_SAMPLES = int(SAMPLE_RATE * CHUNK_DURATION)
WINDOW_SAMPLES = int(SAMPLE_RATE * WINDOW_DURATION)

# bind UDP socket
if __name__ == "__main__":
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    DEST = ("127.0.0.1", 5005)

# handles sending the stream to port
def mic_callback(indata, frames, time_info, status):
    if status:
        print(f"Status: {status}")
    pcm_int16 = (indata[:, 0] * 32767).astype(np.int16)
    sock.sendto(pcm_int16.tobytes(), DEST)

# start mic listening in background
if __name__ == "__main__":
    stream = sd.InputStream(
        samplerate = SAMPLE_RATE,
        channels = 1,
        dtype = "float32",
        blocksize = CHUNK_SAMPLES,
        callback = mic_callback
    )

    with stream:
        print("Mic sender running on 127.0.0.1:5005 (Ctrl + C to stop)...")
        try:
            while True:
                sd.sleep(1000)
        except KeyboardInterrupt:
            pass
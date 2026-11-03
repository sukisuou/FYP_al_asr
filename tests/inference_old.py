# ===== inference code =====
# - passing input into model inference function

import time
import torch, torchaudio
import numpy as np
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
from mic_input import SAMPLE_RATE, WINDOW_SAMPLES
import socket
from utils import to_arabic

# grab the model from huggingface
model_id = "rabah2026/wav2vec2-large-xlsr-53-arabic-quran-v_final"
device = "cuda:0" if torch.cuda.is_available() else "cpu"
device_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

print(f"Loading {model_id} on {device}...")
processor = Wav2Vec2Processor.from_pretrained(model_id)

# load the model in fp16 due to vram limitation
model = Wav2Vec2ForCTC.from_pretrained(
    model_id, 
    torch_dtype = device_dtype
).to(device)
model.eval()

# function for model inference
def transcribe(audio):
    # preprocess input tensor to accept 16kHz
    inputs = processor(audio, sampling_rate = 16000, return_tensors = "pt", padding = True)
    input_values = inputs.input_values.to(device, dtype = device_dtype)

    # run the model without gradient tracking
    with torch.no_grad():
        logits = model(input_values).logits

        # argmax to get the highest probability token id
        predicted_ids = torch.argmax(logits, dim = -1)

        # turn the ids into the string using CTC decoder
        transcription = processor.batch_decode(predicted_ids)[0]
        return transcription

# bind UDP swocket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("127.0.0.1", 5005))

# a rolling buffer of window sample length (3.0 seconds) to keep model from choking
buffer = np.zeros(WINDOW_SAMPLES, dtype = np.float32)

# always waiting for input stream
print("Inference engine waiting for packets on port 5005...")
try:
    while True:
        # grab the real-time bytestream from vercel (UDP for now)
        raw_bytes, _ = sock.recvfrom(65535)
        audio = np.frombuffer(raw_bytes, dtype = np.int16).astype(np.float32) / 32768.0

        # insert new audio at the end
        buffer = np.roll(buffer, -len(audio))
        buffer[-len(audio):] = audio

        # simple energy threshold so we don't infer on pure silence
        rms = np.sqrt(np.mean(audio ** 2))
        if rms < 0.02:
            continue

        # run the inference
        transcription = transcribe(buffer)

        if transcription.strip():
            print(f"Heard: {to_arabic(transcription)}")

except KeyboardInterrupt:
    print("\nStopped.")
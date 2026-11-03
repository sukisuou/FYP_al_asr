# ===== inference code =====
# - passing input into model inference function

import torch
import numpy as np
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor

class ASRInferenceEngine:
    def __init__(self):
        # grab the model from huggingface
        self.model_id = "rabah2026/wav2vec2-large-xlsr-53-arabic-quran-v_final"
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        self.device_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        self.sample_rate = 16000
        self.window_duration = 3.0
        self.silence_threshold = 0.02
    
        # calculate window sample with rolling buffer to keep CTC from choking
        self.window_samples = int(self.sample_rate * self.window_duration)
        self.buffer = np.zeros(self.window_samples, dtype = np.float32)

        # load the processing and model in fp16 due to vram limitation
        print(f"Loading {self.model_id} on {self.device}...")
        self.processor = Wav2Vec2Processor.from_pretrained(self.model_id)
        self.model = Wav2Vec2ForCTC.from_pretrained(
            self.model_id, 
            torch_dtype = self.device_dtype
        ).to(self.device)
        self.model.eval()

    # function for model inference
    def transcribe(self, audio):
        # preprocess input tensor to accept 16kHz
        inputs = self.processor(
            audio, 
            sampling_rate = self.sample_rate, 
            return_tensors = "pt", 
            padding = True
        )
        input_values = inputs.input_values.to(self.device, dtype = self.device_dtype)

        # run the model without gradient tracking
        with torch.no_grad():
            logits = self.model(input_values).logits

            # argmax to get the highest probability token id
            predicted_ids = torch.argmax(logits, dim = -1)

            # turn the ids into the string using CTC decoder
            transcription = self.processor.batch_decode(predicted_ids)[0]

            return transcription

    # handles input PCM bytestream
    def process_chunk(self, raw_bytes):
        # grab the real-time bytestream from vercel (UDP for now)
        audio = np.frombuffer(raw_bytes, dtype = np.int16).astype(np.float32) / 32768.0

        # insert new audio at the end
        self.buffer = np.roll(self.buffer, -len(audio))
        self.buffer[-len(audio):] = audio

        # simple energy threshold so we don't infer on pure silence
        rms = np.sqrt(np.mean(audio ** 2))
        if rms < self.silence_threshold:
            return ""

        return self.transcribe(self.buffer)

    def __call__(self, raw_bytes):
        return self.process_chunk(raw_bytes)


# testing area with UDP
if __name__ == "__main__":
    import socket
    from utils import to_arabic

    # create an inference engine object
    asr = ASRInferenceEngine()

    # bind to UDP
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", 5005))

    print("Inference engine waiting for packets on port 5005...")
    try:
        while True:
            # grab the real-time bytestream from UDP
            raw_bytes, _ = sock.recvfrom(65535)
            transcription = asr(raw_bytes)

            if transcription.strip():
                print(f"Heard: {to_arabic(transcription)}")

    except KeyboardInterrupt:
        print("\nStopped.")
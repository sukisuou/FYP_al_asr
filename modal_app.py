import modal
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from matcher import AyahTracker, data
from inference import ASRInferenceEngine

# modal setup
app = modal.App("al-asr")
image = (
    modal.Image.debian_slim(python_version = "3.11")
    .pip_install(
        "torch",
        "transformers",
        "numpy",
        "rapidfuzz",
        "fastapi[standard]",
        "websockets"
    )
    .add_local_file("quran_clean.json", remote_path = "/root/quran_clean.json")
    .add_local_file("inference.py", remote_path = "/root/inference.py")
    .add_local_file("matcher.py", remote_path = "/root/matcher.py")
)
web_app = FastAPI()

# main function handling the logic
@web_app.websocket("/ws")
async def main(websocket: WebSocket, target_ayah_num: int = 0):
    # initialize tracker with target ayah
    tracker = AyahTracker()
    target_words = data[target_ayah_num]["norm_words"]
    tracker.load(target_words)

    # create an inference engine object
    asr = ASRInferenceEngine()

    # receive raw bytes from WebSocket
    await websocket.accept()

    states = tracker.showStates()
    last_emitted_word = None

    try:
        while True:
            # grab the real-time bytestream from WebSocket
            raw_bytes = await websocket.receive_bytes()
            transcription = asr(raw_bytes)

            # continue if nothing
            if not transcription.strip():
                continue

            # grab the last word to match with ayah
            words = transcription.split()

            # continue if none
            if not words:
                continue
            latest_word = words[-1]
            
            # check if new token pops up
            if latest_word != last_emitted_word:
                cursor = tracker.check(latest_word)
                states = tracker.showStates()
                last_emitted_word = latest_word

                await websocket.send_json({
                    "latest_word": latest_word,
                    "cursor": cursor,
                    "states": states
                })   
    except WebSocketDisconnect:
        print(f"Client disconnected from Ayah {target_ayah_num}")

# runs the backend app
@app.function(gpu = "T4", image = image)
@modal.asgi_app()
def run():
    return web_app
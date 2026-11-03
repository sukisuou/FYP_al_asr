# main code - terminal + local UDP

import socket
from matcher import AyahTracker, data
from inference import ASRInferenceEngine
from utils import to_arabic

# ANSI setup
GREEN, YELLOW, GRAY, RESET = "\033[92m", "\033[93m", "\033[90m", "\033[0m"
COLOR_MAP = {"read": GREEN, "active": YELLOW, "unread": GRAY}

def render_ayah(target_words, states, cursor):
    tokens = []
    for idx, (word, state) in enumerate(zip(target_words, states)):
        reshaped = to_arabic(word)
        color = COLOR_MAP.get(state, "")
        tokens.append(f"{color}{reshaped}{RESET}")

    print(" ".join(tokens[::-1]))

def main(target_ayah_num):
    # initialize tracker with target ayah
    tracker = AyahTracker()
    target_words = data[target_ayah_num]["norm_words"]
    tracker.load(target_words)

    # create an inference engine object
    asr = ASRInferenceEngine()

    # bind to UDP
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", 5005))

    print("Inference engine waiting for packets on port 5005...")
    states = tracker.showStates()
    print("\nTarget ayah:")
    render_ayah(target_words, states, tracker.cursor)
    last_emitted_word = None

    try:
        while True:
            # grab the real-time bytestream from UDP
            raw_bytes, _ = sock.recvfrom(65535)
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
                last_emitted_word = latest_word

                # render the ayah
                states = tracker.showStates()
                matched_target = target_words[cursor] if cursor >= 0 else "-"
                print(f"\nHeard: {to_arabic(latest_word):<12} | Matched: {to_arabic(matched_target)} (idx {cursor})")
                render_ayah(target_words, states, cursor)

    except KeyboardInterrupt:
        print("\nStopped.")


# testing area
if __name__ == "__main__":
    main(target_ayah_num = 0)
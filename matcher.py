# ===== text matcher =====
# - matches the tokens received from inference to the dataset

import json
from rapidfuzz import fuzz
from utils import to_arabic

# 1) load the cleaned quran json
with open("quran_clean.json", "r", encoding = "utf-8") as f:
    data = json.load(f)

# 2) search and match current text using contextual checking (my own idea!! kinda like bigram?)
class AyahTracker:
    def __init__(self):
        self.target_words = []
        self.word_states = []
        self.cursor = -1    # for first word (-1 + 1 = 0)
        self.prev_word = None
        self.threshold = 80
    
    # run with every selection
    def load(self, target_words):
        self.target_words = target_words
        self.word_states = ["unread"] * len(target_words)
        if self.word_states:
            self.word_states[0] = "active"
        self.cursor = -1
        self.prev_word = None

    # handle word matching
    def is_match(self, w1, w2):
        if w1 == w2:    # exact match first
            return True
        # fuzzy match to allow tiny mismatch
        return fuzz.ratio(w1, w2) >= self.threshold

    # handle states (mark unread if restart)
    def update_state(self, new_cursor):
        if new_cursor < 0 or new_cursor >= len(self.target_words):
            return

        # mark everything done as read
        elif self.cursor >= 0:
            self.word_states[self.cursor] = "read"
        
        # backtracking, undo everything
        if new_cursor < self.cursor:
            for i in range(new_cursor + 1, len(self.word_states)):
                self.word_states[i] = "unread"
        
        # new word stays active, not read or unread
        self.word_states[new_cursor] = "active"
        self.cursor = new_cursor

    def check(self, current_word):
        # if current word is in sequence with previous, continue
        if self.cursor + 1 < len(self.target_words) and self.is_match(current_word, self.target_words[self.cursor + 1]):
            self.update_state(self.cursor + 1)

        # if not, find somewhere else (find closest one first though)
        elif self.prev_word is not None:
            candidates = []
            for i in range(len(self.target_words) - 1):
                # check if (i, i + 1) == (prev, current)
                if self.is_match(self.target_words[i], self.prev_word) and self.is_match(self.target_words[i + 1], current_word):
                    candidates.append(i + 1)

            if candidates:
                forward_candidates = [c for c in candidates if c > self.cursor]
                # go forward if possible
                if forward_candidates:
                    best_match = min(forward_candidates, key = lambda idx: idx - self.cursor)
                # find the closest
                else:
                    best_match = min(candidates, key = lambda idx: abs(idx - self.cursor))
                self.update_state(best_match)

        self.prev_word = current_word
        return self.cursor

    def showStates(self):
        return self.word_states

# test
if __name__ == "__main__":
    # ANSI escape codes
    GREEN = "\033[92m"   # read
    YELLOW = "\033[93m"  # active
    GRAY = "\033[90m"    # unread
    RESET = "\033[0m"

    COLOR_MAP = {
        "read": GREEN,
        "active": YELLOW,
        "unread": GRAY
    }

    def colorize(text, state):
        color = COLOR_MAP.get(state, "")
        return f"{color}{text}{RESET}"

    target_data = data[290]
    target_words = target_data["norm_words"]
    test_input = "لله ما في تفاح وما في الارض"
    test_words = test_input.split()
    tracker = AyahTracker()
    tracker.load(target_words)

    print(f"Target sentence: {to_arabic(' '.join(target_words[:7]))}")
    print(f"Input sentence : {to_arabic(test_input)}")
    for current_word in test_words:
        cursor = tracker.check(current_word)
        states = tracker.showStates()
        
        print(f"\n---> Recited: {to_arabic(current_word)} | Cursor: {cursor}")
        for idx, (word, state) in enumerate(zip(target_words[:7], states[:7])):
            marker = "▶" if idx == cursor else " "
            colored_word = colorize(to_arabic(word), state)
            colored_state = colorize(state, state)
            print(f" {marker} [{idx}] {colored_word:<20} -> {colored_state}")
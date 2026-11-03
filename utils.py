import arabic_reshaper
from bidi.algorithm import get_display

# display helper function
def to_arabic(trasncript):
    reshaped_text = arabic_reshaper.reshape(trasncript)
    return get_display(reshaped_text)
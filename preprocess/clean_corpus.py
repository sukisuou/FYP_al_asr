# disclaimer: 
# - data cleaning made by Gemini AI, and self-added some later
# - function: to remove basmala from each surah except al-Fatihah
# - tools used: json, regex, xml (for surah names)

import json
import re
import xml.etree.ElementTree as ET

AR_DIACRITICS = re.compile(
    r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED\u08F0-\u08FF]"
)

# grab the xml
tree = ET.parse("quran-data.xml")
root = tree.getroot()

surah_meta = {}
for sura in root.find("suras").findall("sura"):
    idx = int(sura.attrib["index"])
    surah_meta[idx] = {
        "name_ar": sura.attrib["name"],         # الفاتحة
        "name_translit": sura.attrib["tname"],   # Al-Faatiha
        "name_en": sura.attrib["ename"],         # The Opening
        "total_ayas": int(sura.attrib["ayas"]),
        "type": sura.attrib["type"]              # Meccan / Medinan
    }

# Grab the exact Basmala string directly from line 1|1 of Tanzil
with open("quran-uthmani.txt", "r", encoding="utf-8") as f:
    for line in f:
        if line.startswith("1|1|"):
            # Line is "1|1|بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ\n"
            RAW_BASMALA = line.strip().split("|")[2]
            break

def normalize_arabic(text: str) -> str:
    text = AR_DIACRITICS.sub("", text)
    text = re.sub(r"[إأآٱ]", "ا", text)
    text = re.sub(r"ى", "ي", text)
    text = re.sub(r"ة", "ه", text)
    text = re.sub(r"ؤ", "و", text)
    text = re.sub(r"ئ", "ي", text)
    return " ".join(text.split())

clean_database = []

with open("quran-uthmani.txt", "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        parts = line.split("|")
        surah = int(parts[0])
        ayah = int(parts[1])
        raw_text = parts[2]

        # Strip exact raw Basmala from verse 1 of surahs 2-114
        if surah != 1 and ayah == 1:
            # Check if it starts with the exact Tanzil basmala string
            if raw_text.startswith(RAW_BASMALA):
                raw_text = raw_text[len(RAW_BASMALA):].strip()

        norm_text = normalize_arabic(raw_text)

        meta = surah_meta[surah]
        clean_database.append({
            "surah": surah,
            "surah_name_ar": meta["name_ar"],
            "surah_name_translit": meta["name_translit"],
            "surah_name_en": meta["name_en"],
            "total_ayas":meta["total_ayas"],
            "ayah": ayah,
            "raw_text": raw_text,
            "norm_text": norm_text,
            "raw_words": raw_text.split(),
            "norm_words": norm_text.split()
        })

with open("quran_clean.json", "w", encoding="utf-8") as f:
    json.dump(clean_database, f, ensure_ascii=False, indent=2)

print(f"Done! Saved {len(clean_database)} cleaned Ayahs to quran_clean.json")
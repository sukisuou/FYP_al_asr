import modal

app = modal.App("al-asr")

image = (
    modal.Image.debian_slim(python_version = "3.10")
    .pip_install(
        "torch",
        "transformers",
        "numpy",
        "rapidfuzz",
        "fastapi[standard]",
        "websockets"
    )
    .add_local_file("quran_clean.json", remote_path = "/root/quran_clean.json")
)
"""
fetch_faces.py — Download exactly 25 face images from the Kaggle dataset
"almightyj/person-face-dataset-thispersondoesnotexist" without extracting
all 10,000 images to disk.

Usage:
    task2/.venv311/Scripts/python task4/fetch_faces.py
"""

import os
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

DATASET = "almightyj/person-face-dataset-thispersondoesnotexist"
OUT_DIR = Path(__file__).parent / "faces"
N_FACES = 25
KAGGLE_JSON = Path.home() / ".kaggle" / "kaggle.json"

# ── Preflight ──────────────────────────────────────────────────────────────────
if not KAGGLE_JSON.exists():
    print("ERROR: Kaggle credentials not found at", KAGGLE_JSON)
    sys.exit(1)

try:
    from kaggle import KaggleApi
except ImportError:
    print("ERROR: kaggle package not installed.")
    print("Run:  task2/.venv311/Scripts/pip install kaggle")
    sys.exit(1)

# ── Already done? ──────────────────────────────────────────────────────────────
OUT_DIR.mkdir(parents=True, exist_ok=True)
existing = sorted(OUT_DIR.glob("face_*.jpg"))
if len(existing) >= N_FACES:
    print(f"✓ Already have {len(existing)} face images in {OUT_DIR}. Nothing to do.")
    sys.exit(0)

# ── Authenticate ───────────────────────────────────────────────────────────────
print("Authenticating with Kaggle API…")
api = KaggleApi()
api.authenticate()

# ── Download zip into a temp dir, extract only 25 images ──────────────────────
tmp_dir = Path(tempfile.mkdtemp())
try:
    print(f"Downloading dataset zip (this may take a minute)…")
    api.dataset_download_files(DATASET, path=str(tmp_dir), quiet=False, unzip=False)

    zips = list(tmp_dir.glob("*.zip"))
    if not zips:
        print("ERROR: zip file not found after download.")
        sys.exit(1)
    zip_path = zips[0]
    print(f"Zip downloaded: {zip_path.name} ({zip_path.stat().st_size / 1_048_576:.1f} MB)")

    print(f"Extracting {N_FACES} images…")
    with zipfile.ZipFile(zip_path, "r") as zf:
        img_entries = sorted([
            e for e in zf.namelist()
            if e.lower().endswith((".jpg", ".jpeg", ".png"))
            and not os.path.basename(e).startswith(".")
        ])[:N_FACES]

        if not img_entries:
            print("ERROR: No images found inside zip.")
            sys.exit(1)

        for idx, entry in enumerate(img_entries, start=1):
            data = zf.read(entry)
            out_path = OUT_DIR / f"face_{idx:02d}.jpg"
            out_path.write_bytes(data)
            print(f"  [{idx:2d}/{N_FACES}] {os.path.basename(entry)}  →  {out_path.name}")

finally:
    shutil.rmtree(tmp_dir, ignore_errors=True)

saved = sorted(OUT_DIR.glob("face_*.jpg"))
print(f"\n✓ Done. {len(saved)} face images saved to: {OUT_DIR}")
print("  Restart the Streamlit app — Challenge 1 will now show the police dossier.")

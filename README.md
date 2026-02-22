# Transkrip Video Offline (Whisper)

Aplikasi Python sederhana untuk mentranskrip video menjadi file TXT paragraf kontinu (tanpa timestamp) menggunakan model Whisper lokal.

## Fitur
- Input: file video tunggal atau folder berisi banyak video.
- Output: `.txt` per video, isi berupa paragraf kontinu dari awal sampai akhir.
- Model: `tiny`, `base`, `small` (default), `medium`, `large-v3`.
- Otomatis pilih CPU/GPU (bisa paksa via `--device`).

## Prasyarat
- Windows PowerShell.
- Python 3.11 sangat disarankan. openai-whisper saat ini belum menyediakan wheel resmi untuk Python 3.13 sehingga instalasi dapat gagal.
  - Install Python 3.11 (salah satu):
    - winget: `winget install -e --id Python.Python.3.11`
    - Microsoft Store: Python 3.11
- ffmpeg terpasang dan ada di PATH.
  - Install cepat (salah satu):
    - winget: `winget install --id=FFmpeg.FFmpeg -e`
    - choco:  `choco install ffmpeg -y`

## Instalasi
Di folder proyek ini jalankan:

```powershell
python -m venv .venv ; .\.venv\Scripts\Activate.ps1 ; python -m pip install --upgrade pip ; pip install -r requirements.txt
```
Atau gunakan runner (otomatis memakai Python 3.11 jika ada):
```powershell
.\u005crun_transkrip.bat
```

Catatan Torch: Paket `openai-whisper` akan menarik Torch. Jika pemasangan Torch gagal, Anda bisa memasangnya manual sesuai perangkat:
- CPU-only (Windows):
  ```powershell
  pip install torch --index-url https://download.pytorch.org/whl/cpu
  ```
- NVIDIA CUDA (sesuai versi CUDA driver): lihat https://pytorch.org/get-started/locally/

## Cara Pakai
Transkrip satu file video:
```powershell
python transkrip.py "D:\path\ke\video.mp4"
```

Transkrip semua video dalam folder (rekursif), hasil ke subfolder `transkrip`:
```powershell
python transkrip.py "D:\path\ke\folder-video"
```

Pilih model dan bahasa (contoh bahasa Indonesia):
```powershell
python transkrip.py "D:\path\ke\video.mp4" --model small --language id
```

Pilih device secara manual (cpu/cuda):
```powershell
python transkrip.py "D:\path\ke\video.mp4" --device cpu
```

Pilih folder output khusus:
```powershell
python transkrip.py "D:\path\ke\folder-video" --output-dir "D:\hasil-transkrip"
```

# Jika punya GPU NVIDIA
python transkrip.py "D:\video.mp4" -m medium -d cuda

## Tips
- Model lebih besar → lebih akurat namun lebih lambat dan makan RAM/VRAM.
- Pastikan ruang disk cukup, Whisper akan membuat file audio sementara saat memproses.
- Untuk bahasa campuran, biarkan `--language` kosong agar auto-detect.
 - Jika Anda hanya memiliki Python 3.13, pertimbangkan untuk memasang Python 3.11 khusus proyek ini.

## Lisensi
MIT

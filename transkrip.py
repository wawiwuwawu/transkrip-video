#!/usr/bin/env python3
"""
Transkrip Video ke TXT Paragraf Kontinu (Offline)

Fitur:
- Input: file video tunggal atau folder berisi banyak video.
- Output: file .txt berisi paragraf kontinu dari awal sampai akhir (tanpa timestamp).
- Model: OpenAI Whisper lokal (tiny/base/small/medium/large-v3). Default: small.
- Otomatis pilih CPU/GPU jika tersedia. CPU: fp16 dimatikan otomatis.

Kebutuhan:
- Python 3.9+ (disarankan 3.10/3.11)
- ffmpeg terpasang di PATH
- Paket pip: torch, openai-whisper
"""

from __future__ import annotations

import argparse
import sys
import os
from pathlib import Path
import shutil


VIDEO_EXTS = {
    ".mp4", ".mkv", ".avi", ".mov", ".m4v", ".webm", ".mpg", ".mpeg", ".flv", ".wmv", ".3gp"
}


def ensure_ffmpeg() -> None:
    """Pastikan ffmpeg tersedia di PATH. Jika tidak, berikan pesan bantuan lalu keluar."""
    if shutil.which("ffmpeg") is None:
        msg = (
            "ffmpeg tidak ditemukan di PATH.\n"
            "Silakan install ffmpeg terlebih dahulu. Contoh (PowerShell):\n"
            "  - winget:  winget install --id=FFmpeg.FFmpeg -e  (atau)  winget install --id=Gyan.FFmpeg -e\n"
            "  - choco:   choco install ffmpeg -y\n"
            "Setelah instalasi, pastikan terminal baru mengenali perintah `ffmpeg`."
        )
        print(msg, file=sys.stderr)
        sys.exit(1)


def collect_video_files(input_path: Path) -> list[Path]:
    if input_path.is_file():
        return [input_path]
    files: list[Path] = []
    for p in input_path.rglob("*"):
        if p.suffix.lower() in VIDEO_EXTS and p.is_file():
            files.append(p)
    return sorted(files)


def _try_load_openai_whisper(model_name: str, device_arg: str | None):
    try:
        import torch  # lazy import
        import whisper  # lazy import
    except Exception:
        return None

    device = device_arg if device_arg else ("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Memuat model (openai-whisper): {model_name} (device={device})...")
    model = whisper.load_model(model_name, device=device)
    return {"backend": "whisper", "model": model, "device": device}


def _try_load_faster_whisper(model_name: str, device_arg: str | None):
    try:
        from faster_whisper import WhisperModel  # type: ignore
    except Exception:
        return None

    device = device_arg if device_arg else "cpu"
    compute_type = "float16" if device == "cuda" else "int8"
    print(f"Memuat model (faster-whisper): {model_name} (device={device}, compute_type={compute_type})...")
    model = WhisperModel(model_name, device=device, compute_type=compute_type)
    return {"backend": "faster", "model": model, "device": device}


def load_whisper_model(model_name: str, device_arg: str | None):
    # Coba openai-whisper terlebih dahulu, jika tidak tersedia jatuh ke faster-whisper
    loaded = _try_load_openai_whisper(model_name, device_arg)
    if loaded is None:
        loaded = _try_load_faster_whisper(model_name, device_arg)
    if loaded is None:
        raise RuntimeError(
            "Tidak bisa memuat backend transkrip. Instal salah satu: 'openai-whisper' (butuh torch) atau 'faster-whisper'."
        )
    return loaded


def transcribe_to_paragraph(loaded_model, file_path: Path, language: str | None) -> str:
    """
    Transkripsi satu file video ke paragraf kontinu.
    Menggunakan model.transcribe dari whisper. Hasil text dibersihkan dan dinormalisasi spasi.
    """
    backend = loaded_model["backend"]
    model = loaded_model["model"]
    device = loaded_model["device"]

    print(f"→ Men-transkrip: {file_path.name}")

    if backend == "whisper":
        kwargs = {}
        if language:
            kwargs["language"] = language
        if device == "cpu":
            kwargs["fp16"] = False
        result = model.transcribe(str(file_path), **kwargs)
        text = (result.get("text") or "").strip()
    elif backend == "faster":
        # faster-whisper: transcribe mengembalikan (segments, info)
        segments, _info = model.transcribe(str(file_path), language=language if language else None)
        collected = []
        for seg in segments:
            # seg.text sudah tanpa timestamp, namun bisa ada spasi/linebreak
            if seg and getattr(seg, "text", None) is not None:
                collected.append(seg.text)
        text = " ".join(part.strip() for part in collected if part)
    else:
        raise RuntimeError("Backend tidak dikenali.")

    # normalisasi whitespace menjadi satu spasi; hapus newline agar jadi paragraf kontinu
    text = " ".join(text.split())
    return text


def write_txt(output_dir: Path, source_file: Path, content: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / (source_file.stem + ".txt")
    out_path.write_text(content + "\n", encoding="utf-8")
    return out_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transkrip video ke TXT paragraf kontinu (Whisper)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "input",
        help="Path ke file video atau folder berisi video",
    )
    parser.add_argument(
        "-o", "--output-dir",
        help="Folder output untuk file .txt",
        default=None,
    )
    parser.add_argument(
        "-m", "--model",
        help="Ukuran/tipe model Whisper",
        choices=["tiny", "base", "small", "medium", "large-v3"],
        default="small",
    )
    parser.add_argument(
        "-l", "--language",
        help="Kode bahasa (mis. 'id', 'en'). Kosongkan untuk auto-detect",
        default=None,
    )
    parser.add_argument(
        "-d", "--device",
        help="Pilih device secara manual ('cpu' atau 'cuda'). Kosongkan untuk auto",
        choices=["cpu", "cuda"],
        default=None,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input).expanduser().resolve()

    if not input_path.exists():
        print(f"Path tidak ditemukan: {input_path}", file=sys.stderr)
        return 2

    ensure_ffmpeg()

    try:
        loaded = load_whisper_model(args.model, args.device)
    except Exception as e:
        print("Gagal memuat model Whisper. Pastikan 'torch' dan 'openai-whisper' terpasang.", file=sys.stderr)
        print(f"Detail: {e}", file=sys.stderr)
        return 1

    files = collect_video_files(input_path)
    if not files:
        print("Tidak ada file video yang ditemukan.", file=sys.stderr)
        return 3

    if args.output_dir:
        output_dir = Path(args.output_dir).expanduser().resolve()
    else:
        # default: jika input file → di folder yang sama; jika folder → subfolder 'transkrip'
        if input_path.is_file():
            output_dir = input_path.parent
        else:
            output_dir = input_path / "transkrip"

    print(f"Total video: {len(files)} | Output: {output_dir}")

    ok = 0
    for f in files:
        try:
            text = transcribe_to_paragraph(loaded, f, args.language)
            out_path = write_txt(output_dir, f, text)
            print(f"  ✓ Selesai: {out_path}")
            ok += 1
        except KeyboardInterrupt:
            print("Dibatalkan oleh pengguna.", file=sys.stderr)
            return 130
        except Exception as e:
            print(f"  ✗ Gagal: {f} → {e}", file=sys.stderr)

    print(f"Selesai. Berhasil: {ok}/{len(files)}")
    return 0 if ok == len(files) else 4


if __name__ == "__main__":
    raise SystemExit(main())

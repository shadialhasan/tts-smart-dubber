# 🎬 tts-smart-dubber

> **Topics:** `video-dubbing` `text-to-speech` `tts` `voiceover` `audio-sync` `ffmpeg` `video-localization`


[![Release](https://img.shields.io/badge/Release-v1.0.0-blue.svg)](https://github.com/MobileConduit/tts-smart-dubber/releases/tag/v1.0.0)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![CI/CD](https://github.com/MobileConduit/tts-smart-dubber/actions/workflows/ci.yml/badge.svg)](https://github.com/MobileConduit/tts-smart-dubber/actions/workflows/ci.yml)
[![Engine: FFmpeg](https://img.shields.io/badge/Engine-FFmpeg-blue.svg)](https://ffmpeg.org)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![Tests: Pytest](https://img.shields.io/badge/Tests-Pytest-green.svg)](https://docs.pytest.org)

An enterprise-grade video dubbing and audio replacement pipeline designed to seamlessly integrate AI-generated speech (Edge-TTS, ElevenLabs, XTTS, Coqui) with existing video assets. Preserves pristine original video bitstreams with zero generation loss (`-c:v copy`) while re-encoding and remuxing replacement audio, validating acoustic sync, and exporting comprehensive metrics.

---

## 🏗️ Architecture & Pipeline Flow

The following Mermaid diagram outlines the end-to-end audio extraction, synchronization verification, and lossless video remuxing pipeline:

```mermaid
flowchart TD
    subgraph Inputs ["Input Artifacts"]
        V["Source Video (.mp4 / .mkv / .mov)"]
        A["Synthesized TTS Audio (.wav / .mp3)"]
    end

    subgraph Extraction ["Audio Extraction & Inspection"]
        EXT["FFmpeg PCM Extractor<br/>(-vn -acodec pcm_s16le)"]
        OA["Original Audio Track (.wav)"]
        MET1["Audio Acoustic Profiler<br/>(RMS, Peak, Duration)"]
        MET2["Dub Audio Profiler<br/>(RMS, Peak, Duration)"]
    end

    subgraph SyncEngine ["Synchronization Engine"]
        SYNC["Drift Calculator & Validator<br/>(Delta = |Dub - Orig| <= Tolerance)"]
        REP["Sync Validation Report & JSON Exporter"]
    end

    subgraph Muxing ["Lossless Video Remuxing"]
        MUX["FFmpeg Stream Multiplexer<br/>(-c:v copy -c:a aac -shortest)"]
        OUT["Dubbed Video Output (.mp4)"]
    end

    V --> EXT
    EXT --> OA
    OA --> MET1
    A --> MET2
    MET1 --> SYNC
    MET2 --> SYNC
    SYNC --> REP
    V --> MUX
    A --> MUX
    MUX --> OUT

    classDef proc fill:#1e293b,stroke:#3b82f6,stroke-width:2px,color:#f8fafc;
    classDef io fill:#0f172a,stroke:#10b981,stroke-width:2px,color:#f8fafc;
    class V,A,OA,OUT io;
    class EXT,MET1,MET2,SYNC,REP,MUX proc;
```

---

## ✨ Features

- **Zero-Loss Video Remuxing:** Retains 100% of original visual quality using FFmpeg stream copy (`-c:v copy`).
- **Automated Synchronization Checks:** Compares original voice track duration against synthesized TTS track to flag potential lip-sync drifts.
- **Verbose Acoustic Metrics Export:** Probes frame counts, sample rates, channels, RMS energy, and peak amplitudes into structured JSON.
- **Environment Configuration:** Full support for `.env` files to configure codecs, bitrates, temp folders, and tolerances.
- **Automated Testing & CI/CD:** Comprehensive Pytest test suite with multi-version GitHub Actions CI pipeline.

---

## 🚀 Installation & Setup

### Prerequisites
- Python 3.10 or higher
- System FFmpeg installed and accessible via system PATH

```bash
# Clone the repository
git clone https://github.com/MobileConduit/tts-smart-dubber.git
cd tts-smart-dubber

# Install dependencies
pip install -r requirements.txt
```

### Environment Configuration
Copy the example environment file:
```bash
cp .env.example .env
```

| Variable | Default | Description |
| :--- | :--- | :--- |
| `FFMPEG_BINARY` | `ffmpeg` | Path or name of FFmpeg executable |
| `DUBBER_AUDIO_CODEC` | `aac` | Target audio codec for remuxing |
| `DUBBER_AUDIO_BITRATE` | `192k` | Output audio bitrate |
| `DUBBER_TEMP_DIR` | `_dub_temp` | Temporary directory for intermediate tracks |
| `SYNC_TOLERANCE_SECONDS` | `1.5` | Allowed duration drift before warning |

---

## 💻 CLI Usage

### Basic Dubbing
```bash
python dubber.py --video input.mp4 --audio arabic_voiceover.wav --output dubbed_video.mp4
```

### Synchronized Dubbing with Verbose Metrics Export
```bash
python dubber.py \
  --video documentary.mp4 \
  --audio synthesized_speech.wav \
  --output documentary_dubbed.mp4 \
  --codec aac \
  --bitrate 256k \
  --validate-sync \
  --sync-tolerance 1.0 \
  --export-metrics sync_metrics.json
```

---

## 🧪 Testing

Execute the automated test suite locally:
```bash
pytest -v tests/
```

---

## 👤 Author & Maintainer

**Eng. MHD. Shadi AL-Hasan**  
- **Role:** Executive CTO & Enterprise Solutions Architect  
- **Email:** [mhd.shadi.alhasan@gmail.com](mailto:mhd.shadi.alhasan@gmail.com)  
- **Phone / WhatsApp:** [+963934005922](tel:+963934005922)  
- **Location:** Damascus, Syria  
- **GitHub:** [MobileConduit](https://github.com/MobileConduit)  

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.  
Copyright (c) 2026 **MHD. Shadi AL-Hasan**. All rights reserved.
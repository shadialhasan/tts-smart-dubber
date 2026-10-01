# 🎬 tts-smart-dubber

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Tool: FFmpeg](https://img.shields.io/badge/Engine-FFmpeg-blue.svg)](https://ffmpeg.org)

Pipeline script designed to streamline the integration of AI-generated audio/dubbing (XTTS, ElevenLabs, Edge-TTS) with video footage. Copies the original high-resolution video stream with zero generation loss (`-c:v copy`) while remuxing the new translated/cloned voice track.

## 🚀 Quick Usage
```bash
python dubber.py --video documentary.mp4 --audio arabic_voiceover.wav --output documentary_arabic.mp4
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


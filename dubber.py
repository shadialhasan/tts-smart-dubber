# -*- coding: utf-8 -*-
"""
Smart Video Dubbing & Audio Replacement Pipeline
Author: Eng. MHD. Shadi AL-Hasan <mhd.shadi.alhasan@gmail.com>
Phone: +963934005922
Copyright (c) 2026 MHD. Shadi AL-Hasan
"""

import os
import subprocess
import argparse
from pathlib import Path

class VideoDubber:
    def __init__(self, video_path: str, output_path: str = None):
        self.video_path = Path(video_path)
        self.output_path = Path(output_path) if output_path else self.video_path.with_name(f"dubbed_{self.video_path.name}")
        self.temp_dir = self.video_path.parent / "_dub_temp"
        self.temp_dir.mkdir(exist_ok=True)

    def extract_audio(self) -> Path:
        """Extracts original audio track from video as WAV."""
        audio_out = self.temp_dir / "original_audio.wav"
        cmd = [
            "ffmpeg", "-y", "-i", str(self.video_path),
            "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2",
            str(audio_out)
        ]
        print(f"[*] Extracting audio: {' '.join(cmd)}")
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return audio_out

    def replace_audio_track(self, new_audio_path: Path):
        """Muxes new audio track with the original video stream without re-encoding video."""
        cmd = [
            "ffmpeg", "-y",
            "-i", str(self.video_path),
            "-i", str(new_audio_path),
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
            str(self.output_path)
        ]
        print(f"[*] Muxing dubbed audio into video...")
        subprocess.run(cmd, check=True)
        print(f"[+] Final dubbed video produced at: {self.output_path}")

def main():
    parser = argparse.ArgumentParser(description="Automate audio track replacement and dubbing for video files.")
    parser.add_argument("--video", "-v", required=True, help="Input video file")
    parser.add_argument("--audio", "-a", required=True, help="New synthesized TTS audio file (.wav/.mp3)")
    parser.add_argument("--output", "-o", default=None, help="Output dubbed video file")
    args = parser.parse_args()

    dubber = VideoDubber(args.video, args.output)
    dubber.replace_audio_track(Path(args.audio))

if __name__ == "__main__":
    main()

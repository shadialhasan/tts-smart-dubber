# -*- coding: utf-8 -*-
"""
Smart Video Dubbing & Audio Replacement Pipeline
Author: Eng. MHD. Shadi AL-Hasan <mhd.shadi.alhasan@gmail.com>
Phone: +963934005922
Copyright (c) 2026 MHD. Shadi AL-Hasan
"""

import os
import sys
import wave
import struct
import math
import json
import subprocess
import argparse
from pathlib import Path
from typing import Optional, Dict, Any


def get_env_or_default(key: str, default: str) -> str:
    """Reads environment variable with fallback default."""
    return os.environ.get(key, default)


class VideoDubber:
    def __init__(
        self,
        video_path: str,
        output_path: Optional[str] = None,
        audio_codec: Optional[str] = None,
        audio_bitrate: Optional[str] = None,
        ffmpeg_bin: Optional[str] = None
    ):
        self.video_path = Path(video_path)
        self.output_path = (
            Path(output_path)
            if output_path
            else self.video_path.with_name(f"dubbed_{self.video_path.name}")
        )
        self.temp_dir = self.video_path.parent / get_env_or_default("DUBBER_TEMP_DIR", "_dub_temp")
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        self.audio_codec = audio_codec or get_env_or_default("DUBBER_AUDIO_CODEC", "aac")
        self.audio_bitrate = audio_bitrate or get_env_or_default("DUBBER_AUDIO_BITRATE", "192k")
        self.ffmpeg_bin = ffmpeg_bin or get_env_or_default("FFMPEG_BINARY", "ffmpeg")

    def extract_audio(self) -> Path:
        """Extracts original audio track from video as WAV."""
        audio_out = self.temp_dir / "original_audio.wav"
        cmd = [
            self.ffmpeg_bin, "-y", "-i", str(self.video_path),
            "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2",
            str(audio_out)
        ]
        print(f"[*] Extracting audio: {' '.join(cmd)}")
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return audio_out

    def replace_audio_track(self, new_audio_path: Path) -> Path:
        """Muxes new audio track with the original video stream without re-encoding video."""
        new_audio_path = Path(new_audio_path)
        cmd = [
            self.ffmpeg_bin, "-y",
            "-i", str(self.video_path),
            "-i", str(new_audio_path),
            "-c:v", "copy",
            "-c:a", self.audio_codec, "-b:a", self.audio_bitrate,
            "-map", "0:v:0",
            "-map", "1:a:0",
            "-shortest",
            str(self.output_path)
        ]
        print(f"[*] Muxing dubbed audio into video...")
        subprocess.run(cmd, check=True)
        print(f"[+] Final dubbed video produced at: {self.output_path}")
        return self.output_path

    def get_audio_metrics(self, audio_file: Path) -> Dict[str, Any]:
        """Calculates verbose acoustic and technical metrics for an audio file."""
        audio_path = Path(audio_file)
        metrics: Dict[str, Any] = {
            "file_name": audio_path.name,
            "file_size_bytes": audio_path.stat().st_size if audio_path.exists() else 0,
            "format": audio_path.suffix.lstrip(".").lower(),
        }

        # If WAV file, extract accurate frame-level statistics
        if audio_path.suffix.lower() == ".wav" and audio_path.exists():
            try:
                with wave.open(str(audio_path), "rb") as wf:
                    channels = wf.getnchannels()
                    framerate = wf.getframerate()
                    n_frames = wf.getnframes()
                    sampwidth = wf.getsampwidth()
                    duration = n_frames / float(framerate) if framerate > 0 else 0.0

                    raw_data = wf.readframes(n_frames)
                    rms = 0.0
                    peak = 0.0

                    if sampwidth == 2 and n_frames > 0:
                        total_samples = n_frames * channels
                        fmt = f"<{total_samples}h"
                        samples = struct.unpack(fmt, raw_data)
                        if samples:
                            sum_sq = sum(s * s for s in samples)
                            rms = math.sqrt(sum_sq / len(samples))
                            peak = max(abs(s) for s in samples)

                    metrics.update({
                        "channels": channels,
                        "sample_rate_hz": framerate,
                        "sample_width_bytes": sampwidth,
                        "frame_count": n_frames,
                        "duration_seconds": round(duration, 3),
                        "peak_amplitude": peak,
                        "rms_energy": round(rms, 2),
                    })
            except Exception as e:
                metrics["read_error"] = str(e)
        return metrics

    def validate_sync(
        self, original_audio: Path, dubbed_audio: Path, tolerance_seconds: float = 1.5
    ) -> Dict[str, Any]:
        """Validates duration alignment between original and dubbed audio."""
        orig_metrics = self.get_audio_metrics(original_audio)
        dub_metrics = self.get_audio_metrics(dubbed_audio)

        orig_dur = orig_metrics.get("duration_seconds", 0.0)
        dub_dur = dub_metrics.get("duration_seconds", 0.0)
        delta = dub_dur - orig_dur
        drift_pct = (abs(delta) / orig_dur * 100) if orig_dur > 0 else 0.0
        in_sync = abs(delta) <= tolerance_seconds

        sync_report = {
            "original_duration_seconds": orig_dur,
            "dubbed_duration_seconds": dub_dur,
            "duration_delta_seconds": round(delta, 3),
            "drift_percentage": round(drift_pct, 2),
            "tolerance_seconds": tolerance_seconds,
            "in_sync": in_sync,
        }

        if not in_sync:
            print(
                f"[!] WARNING: Potential lip-sync mismatch! Delta: {delta:.2f}s "
                f"(Exceeds {tolerance_seconds}s tolerance)"
            )
        else:
            print(f"[+] Audio synchronization verified within {tolerance_seconds}s tolerance.")

        return sync_report

    @staticmethod
    def export_metrics(metrics_data: Dict[str, Any], output_path: Path) -> Path:
        """Exports metrics dictionary to a pretty formatted JSON file."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(metrics_data, f, indent=2)
        print(f"[+] Audio metrics successfully exported to: {output_path}")
        return output_path


def parse_args(args=None):
    parser = argparse.ArgumentParser(
        description="Automate audio track replacement and dubbing for video files with synchronization checks."
    )
    parser.add_argument("--video", "-v", required=True, help="Input video file")
    parser.add_argument("--audio", "-a", required=True, help="New synthesized TTS audio file (.wav/.mp3)")
    parser.add_argument("--output", "-o", default=None, help="Output dubbed video file")
    parser.add_argument("--codec", "-c", default=None, help="Audio codec (default: aac)")
    parser.add_argument("--bitrate", "-b", default=None, help="Audio bitrate (default: 192k)")
    parser.add_argument(
        "--validate-sync",
        action="store_true",
        help="Extract and validate audio duration sync against original video audio",
    )
    parser.add_argument(
        "--sync-tolerance",
        type=float,
        default=float(get_env_or_default("SYNC_TOLERANCE_SECONDS", "1.5")),
        help="Allowed duration drift in seconds (default: 1.5)",
    )
    parser.add_argument(
        "--export-metrics",
        default=None,
        help="Path to export verbose audio metrics and synchronization report (JSON)",
    )
    return parser.parse_args(args)


def main():
    args = parse_args()
    dubber = VideoDubber(
        video_path=args.video,
        output_path=args.output,
        audio_codec=args.codec,
        audio_bitrate=args.bitrate,
    )

    metrics_export: Dict[str, Any] = {
        "video_input": str(dubber.video_path),
        "audio_input": str(args.audio),
        "output_path": str(dubber.output_path),
    }

    if args.validate_sync or args.export_metrics:
        try:
            print("[*] Performing audio synchronization analysis...")
            orig_audio = dubber.extract_audio()
            sync_report = dubber.validate_sync(
                orig_audio, Path(args.audio), tolerance_seconds=args.sync_tolerance
            )
            metrics_export["sync_report"] = sync_report
            metrics_export["original_audio_metrics"] = dubber.get_audio_metrics(orig_audio)
        except Exception as e:
            print(f"[!] Sync validation skipped due to extraction error: {e}")

    dub_metrics = dubber.get_audio_metrics(Path(args.audio))
    metrics_export["dubbed_audio_metrics"] = dub_metrics

    dubber.replace_audio_track(Path(args.audio))

    if args.export_metrics:
        dubber.export_metrics(metrics_export, Path(args.export_metrics))


if __name__ == "__main__":
    main()

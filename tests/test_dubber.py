# -*- coding: utf-8 -*-
"""
Automated Unit Tests for Smart Video Dubber
Author: Eng. MHD. Shadi AL-Hasan <mhd.shadi.alhasan@gmail.com>
"""

import sys
import wave
import struct
import math
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dubber import VideoDubber, parse_args, get_env_or_default


def create_synthetic_wav(file_path: Path, duration_seconds: float = 1.0, sample_rate: int = 44100, channels: int = 1, freq: float = 440.0):
    """Generates a valid PCM 16-bit WAV file for testing purposes."""
    n_frames = int(duration_seconds * sample_rate)
    with wave.open(str(file_path), "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        
        frames = bytearray()
        for i in range(n_frames):
            t = i / float(sample_rate)
            val = int(16000 * math.sin(2 * math.pi * freq * t))
            for _ in range(channels):
                frames.extend(struct.pack("<h", val))
        wf.writeframes(frames)


class TestCliArgs:
    """Tests for CLI Argument Parser."""

    def test_cli_requires_video_and_audio(self):
        with pytest.raises(SystemExit):
            parse_args([])

        with pytest.raises(SystemExit):
            parse_args(["--video", "input.mp4"])

        with pytest.raises(SystemExit):
            parse_args(["--audio", "audio.wav"])

    def test_cli_default_arguments(self):
        args = parse_args(["--video", "input.mp4", "--audio", "voice.wav"])
        assert args.video == "input.mp4"
        assert args.audio == "voice.wav"
        assert args.output is None
        assert args.codec is None
        assert args.bitrate is None
        assert args.validate_sync is False
        assert args.export_metrics is None
        assert args.sync_tolerance == 1.5

    def test_cli_custom_arguments(self):
        args = parse_args([
            "-v", "film.mp4",
            "-a", "dub.wav",
            "-o", "out.mp4",
            "-c", "libopus",
            "-b", "256k",
            "--validate-sync",
            "--sync-tolerance", "0.5",
            "--export-metrics", "metrics.json"
        ])
        assert args.video == "film.mp4"
        assert args.audio == "dub.wav"
        assert args.output == "out.mp4"
        assert args.codec == "libopus"
        assert args.bitrate == "256k"
        assert args.validate_sync is True
        assert args.sync_tolerance == 0.5
        assert args.export_metrics == "metrics.json"


class TestVideoDubber:
    """Tests for VideoDubber Core Pipeline."""

    def test_initialization_defaults(self, tmp_path):
        vid = tmp_path / "sample.mp4"
        vid.touch()

        dubber = VideoDubber(str(vid))
        assert dubber.video_path == vid
        assert dubber.output_path == tmp_path / "dubbed_sample.mp4"
        assert dubber.temp_dir.exists()
        assert dubber.audio_codec == "aac"
        assert dubber.audio_bitrate == "192k"

    def test_initialization_custom(self, tmp_path):
        vid = tmp_path / "clip.mp4"
        out = tmp_path / "custom_out.mp4"
        vid.touch()

        dubber = VideoDubber(
            video_path=str(vid),
            output_path=str(out),
            audio_codec="mp3",
            audio_bitrate="320k",
            ffmpeg_bin="/usr/bin/ffmpeg"
        )
        assert dubber.output_path == out
        assert dubber.audio_codec == "mp3"
        assert dubber.audio_bitrate == "320k"
        assert dubber.ffmpeg_bin == "/usr/bin/ffmpeg"

    @patch("subprocess.run")
    def test_extract_audio_command(self, mock_run, tmp_path):
        vid = tmp_path / "source.mp4"
        vid.touch()
        dubber = VideoDubber(str(vid))

        audio_path = dubber.extract_audio()
        assert audio_path == dubber.temp_dir / "original_audio.wav"
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "ffmpeg"
        assert "-y" in cmd
        assert str(vid) in cmd
        assert "-vn" in cmd
        assert "pcm_s16le" in cmd

    @patch("subprocess.run")
    def test_replace_audio_track_command(self, mock_run, tmp_path):
        vid = tmp_path / "source.mp4"
        aud = tmp_path / "cloned.wav"
        vid.touch()
        aud.touch()

        dubber = VideoDubber(str(vid), audio_codec="aac", audio_bitrate="192k")
        result = dubber.replace_audio_track(aud)

        assert result == dubber.output_path
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "-c:v" in cmd and "copy" in cmd
        assert "-c:a" in cmd and "aac" in cmd
        assert "-b:a" in cmd and "192k" in cmd
        assert "-shortest" in cmd
        assert str(dubber.output_path) in cmd

    def test_audio_metrics_calculation(self, tmp_path):
        wav_file = tmp_path / "test_synth.wav"
        create_synthetic_wav(wav_file, duration_seconds=1.5, sample_rate=44100, channels=2)

        dubber = VideoDubber(str(tmp_path / "dummy.mp4"))
        metrics = dubber.get_audio_metrics(wav_file)

        assert metrics["file_name"] == "test_synth.wav"
        assert metrics["channels"] == 2
        assert metrics["sample_rate_hz"] == 44100
        assert metrics["duration_seconds"] == 1.5
        assert metrics["peak_amplitude"] > 0
        assert metrics["rms_energy"] > 0

    def test_validate_sync_detection(self, tmp_path):
        orig_wav = tmp_path / "orig.wav"
        dub_wav_good = tmp_path / "dub_good.wav"
        dub_wav_bad = tmp_path / "dub_bad.wav"

        create_synthetic_wav(orig_wav, duration_seconds=2.0)
        create_synthetic_wav(dub_wav_good, duration_seconds=2.2)  # delta 0.2s (< 1.5s tolerance)
        create_synthetic_wav(dub_wav_bad, duration_seconds=4.5)   # delta 2.5s (> 1.5s tolerance)

        dubber = VideoDubber(str(tmp_path / "dummy.mp4"))

        # In-sync case
        report_good = dubber.validate_sync(orig_wav, dub_wav_good, tolerance_seconds=1.5)
        assert report_good["in_sync"] is True
        assert abs(report_good["duration_delta_seconds"] - 0.2) < 0.05

        # Out-of-sync case
        report_bad = dubber.validate_sync(orig_wav, dub_wav_bad, tolerance_seconds=1.5)
        assert report_bad["in_sync"] is False
        assert abs(report_bad["duration_delta_seconds"] - 2.5) < 0.05

    def test_export_metrics(self, tmp_path):
        export_file = tmp_path / "metrics_output.json"
        data = {"model": "XTTS", "confidence": 0.98}

        dubber = VideoDubber(str(tmp_path / "dummy.mp4"))
        res = dubber.export_metrics(data, export_file)

        assert res.exists()
        with open(res, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        assert loaded == data

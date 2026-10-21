"""Offline Korean narration. Requires the documented local CC0 KSS model.

No network, authentication, voice cloning, or paid API calls.
"""
import hashlib
import json
import subprocess
from pathlib import Path

from .project import ROOT, OUTPUT, atomic_json


def main():
    import sherpa_onnx
    import soundfile as sf
    import numpy as np
    film = json.loads((ROOT / "config/first-film.json").read_text())
    model = OUTPUT / "models/vits-mimic3-ko_KO-kss_low"
    config = sherpa_onnx.OfflineTtsConfig(
        model=sherpa_onnx.OfflineTtsModelConfig(
            vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                model=str(model / "ko_KO-kss_low.onnx"),
                tokens=str(model / "tokens.txt"), data_dir=str(model / "espeak-ng-data")),
            num_threads=2, debug=False), max_num_sentences=1)
    tts = sherpa_onnx.OfflineTts(config)
    directory = OUTPUT / "first-film/audio"
    directory.mkdir(parents=True, exist_ok=True)
    rate = tts.sample_rate
    track = np.zeros(round(film["duration"] * rate), dtype=np.float32)
    report = []
    for n, line in enumerate(film["narration"]):
        # The model does not contain a question-mark phoneme; sentence punctuation
        # is normalized only for synthesis, while captions retain questions.
        audio = tts.generate(line["text"].replace("?", "."), sid=0, speed=1.0)
        raw = directory / f"line_{n:02}_raw.wav"
        adjusted = directory / f"line_{n:02}.wav"
        sf.write(raw, audio.samples, rate)
        raw_seconds = len(audio.samples) / rate
        available = line["end"] - line["start"] - 0.20
        tempo = max(1.0, raw_seconds / available)
        if tempo > 1.25:
            raise ValueError(f"Line {n} is too long; edit text instead of rushing it.")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(raw), "-af",
                        f"atempo={tempo:.8f},afade=t=in:d=0.015,afade=t=out:st={max(0, raw_seconds / tempo - .025):.6f}:d=0.025",
                        str(adjusted)], check=True)
        samples, actual_rate = sf.read(adjusted, dtype="float32")
        assert actual_rate == rate
        start = round((line["start"] + 0.08) * rate)
        if start + len(samples) > round(line["end"] * rate):
            raise ValueError("Narration would cross its edit boundary.")
        track[start:start + len(samples)] = samples
        report.append({"line": n, "start": line["start"] + .08,
                       "speech_seconds": len(samples) / rate, "tempo": tempo})
    sf.write(directory / "narration_raw.wav", track, rate)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(directory / "narration_raw.wav"),
                    "-af", "loudnorm=I=-16:TP=-1.5:LRA=7", "-ar", "48000",
                    str(directory / "narration.wav")], check=True)
    atomic_json(directory / "timing.json", {"model_sha256": hashlib.sha256(
        (model / "ko_KO-kss_low.onnx").read_bytes()).hexdigest(), "lines": report})
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

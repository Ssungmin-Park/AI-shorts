import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs"


def load_project(path=None):
    project = json.loads(Path(path or ROOT / "config/scenes.json").read_text(encoding="utf-8"))
    end = 0
    ids = set()
    for scene in project["scenes"]:
        if scene["id"] in ids or scene["start"] != end or scene["end"] <= end:
            raise ValueError("Scene IDs must be unique and the timeline must be continuous.")
        ids.add(scene["id"])
        end = scene["end"]
        reference = ROOT / project["references"][scene["reference"]]
        if not reference.is_file():
            raise ValueError(f"Missing image: {reference.name}")
        if len(scene["prompt"].encode("utf-16-le")) // 2 > 1000:
            raise ValueError(f"Scene {scene['id']}: prompt exceeds 1000 UTF-16 units.")
    if end != 60:
        raise ValueError("The edit must be exactly 60 seconds.")
    return project


def request_for(project, scene):
    """Generation lengths are separate from editing lengths; trim, never stretch."""
    image = ROOT / project["references"][scene["reference"]]
    return {
        "scene_id": scene["id"],
        "model": "gen4_turbo",
        "ratio": "720:1280",
        "duration": 5 if scene["end"] - scene["start"] <= 5 else 10,
        "edit_duration": scene["end"] - scene["start"],
        "image": str(image.relative_to(ROOT)),
        "image_sha256": hashlib.sha256(image.read_bytes()).hexdigest(),
        "prompt_text": scene["prompt"],
    }


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def srt_time(seconds):
    return f"{seconds // 3600:02}:{seconds // 60 % 60:02}:{seconds % 60:02},000"


def export_plan(project):
    OUTPUT.mkdir(exist_ok=True)
    requests = [request_for(project, scene) for scene in project["scenes"]]
    atomic_json(OUTPUT / "plan.json", requests)
    prompts, narration, subtitles = [], [], []
    for scene in project["scenes"]:
        prompts.append(f"SCENE {scene['id']:02} | {scene['start']}–{scene['end']}s | {scene['reference']}\n{scene['prompt']}\n")
        narration.append(f"{scene['start']:02}–{scene['end']:02}초: {scene['narration']}")
        subtitles.append(f"{scene['id']}\n{srt_time(scene['start'])} --> {srt_time(scene['end'])}\n{scene['caption']}\n")
    for name, lines in [("prompts.txt", prompts), ("narration.txt", narration), ("captions.srt", subtitles)]:
        (OUTPUT / name).write_text("\n".join(lines), encoding="utf-8")
    print(f"Plan: 10 scenes / 60s edit / {sum(r['duration'] for r in requests)}s requested generation")
    print("No API request was sent. Files saved to outputs/.")

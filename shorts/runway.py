"""Only generate_scene(execute=True) may contact Runway. No automatic paid retries."""
import base64
import hashlib
import io
import json
import os
import time
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

from .project import OUTPUT, ROOT, atomic_json, request_for


def image_uri(path):
    from PIL import Image, ImageOps
    with Image.open(path) as original:
        image = ImageOps.exif_transpose(original).convert("RGB")
        image.thumbnail((1280, 1280))
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=94)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    if len(encoded) > 4_500_000:
        raise ValueError("Reference image is too large for a data URI.")
    return "data:image/jpeg;base64," + encoded


def generate_scene(project, scene, execute=False, client=None, timeout=1800, poll=10, output_dir=None):
    request = request_for(project, scene)
    if not execute:
        print(json.dumps(request, ensure_ascii=False, indent=2))
        print("DRY RUN: no API request. --execute may spend credits.")
        return
    if client is None:
        from dotenv import load_dotenv
        from runwayml import RunwayML
        load_dotenv(ROOT / ".env")
        if not os.getenv("RUNWAYML_API_SECRET"):
            raise ValueError("Set RUNWAYML_API_SECRET in a private .env file. Do not put it in GitHub or chat.")
        client = RunwayML(max_retries=0, timeout=60)
    directory = Path(output_dir) if output_dir is not None else OUTPUT
    job_path = directory / "jobs" / f"scene_{scene['id']:02}.json"
    fingerprint = hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()
    state = json.loads(job_path.read_text()) if job_path.exists() else None
    if state and state["fingerprint"] != fingerprint:
        raise ValueError("This scene has an existing job for different settings. Review it before generating a new take.")
    if state and not state.get("id"):
        raise ValueError("Submission was interrupted. Check the Runway dashboard and recover the task ID before retrying.")
    if state is None:
        uri = image_uri(ROOT / request["image"])
        state = {"fingerprint": fingerprint, "status": "SUBMITTING", "request": request}
        atomic_json(job_path, state)
        try:
            task = client.image_to_video.create(
                model=request["model"], ratio=request["ratio"], duration=request["duration"],
                prompt_image=uri, prompt_text=request["prompt_text"],
            )
        except Exception as error:
            # An uncertain submission must never be automatically charged a second time.
            raise RuntimeError(f"Submission stopped ({type(error).__name__}). Check the dashboard before retrying.") from None
        state.update(id=task.id, status="PENDING")
        atomic_json(job_path, state)
    clip = directory / "clips" / f"scene_{scene['id']:02}.mp4"
    if state["status"] == "SUCCEEDED" and clip.is_file() and clip.stat().st_size:
        print(f"Already saved: {clip.name}")
        return
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            task = client.tasks.retrieve(state["id"])
        except Exception as error:
            raise RuntimeError(f"Status check stopped ({type(error).__name__}). Rerun the same command to resume.") from None
        state["status"] = task.status
        atomic_json(job_path, state)
        print(f"Scene {scene['id']:02}: {task.status}", flush=True)
        if task.status in {"FAILED", "CANCELLED"}:
            raise RuntimeError("Runway task failed or was cancelled. Review the dashboard; no replacement was submitted.")
        if task.status == "SUCCEEDED":
            if not task.output or urlparse(task.output[0]).scheme != "https":
                raise RuntimeError("Runway returned no HTTPS video output.")
            clip.parent.mkdir(parents=True, exist_ok=True)
            temporary = clip.with_suffix(".part")
            try:
                with urlopen(task.output[0], timeout=120) as response, temporary.open("wb") as target:
                    while block := response.read(1024 * 1024):
                        target.write(block)
                if not temporary.stat().st_size:
                    raise RuntimeError("Downloaded video was empty.")
                temporary.replace(clip)
            except Exception as error:
                raise RuntimeError(f"Download stopped ({type(error).__name__}). Rerun to download the same task.") from None
            print(f"Saved: {clip.name}")
            return
        time.sleep(poll)
    raise RuntimeError("Polling timed out. The task ID is saved; rerun the same command to resume.")

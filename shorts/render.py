"""FFmpeg-only local storyboard and final clip assembly. No network requests."""
import json
import shutil
import subprocess

from .project import OUTPUT, ROOT, export_plan

FPS = 24


def run(arguments):
    process = subprocess.run(arguments, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if process.returncode:
        raise RuntimeError(f"{arguments[0]} failed:\n{process.stderr[-2500:]}")
    return process.stdout


def ass_time(seconds):
    return f"{seconds // 3600}:{seconds // 60 % 60:02}:{seconds % 60:02}.00"


def ass_text(text):
    # Treat configuration strings as text, not ASS formatting commands.
    return text.replace("\\", "").replace("{", "(").replace("}", ")").replace("\n", "\\N")


def write_overlay(project, directory, preview):
    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280
WrapStyle: 0
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Main,Noto Sans CJK KR,35,&H00FFFFFF,&H00FFFFFF,&H00140B06,&H80000000,-1,0,0,0,100,100,0,0,1,2,1,2,48,48,200,1
Style: Caption,Noto Sans CJK KR,27,&H00FFFFFF,&H00FFFFFF,&H00140B06,&H80000000,0,0,0,0,100,100,0,0,1,1.5,1,2,48,48,108,1
Style: Label,Noto Sans CJK KR,18,&H00F9E44D,&H00FFFFFF,&H00140B06,&H80000000,-1,0,0,0,100,100,1,0,1,1,0,8,30,30,52,1
Style: Notice,Noto Sans CJK KR,16,&H00DDDDDD,&H00FFFFFF,&H00140B06,&H80000000,0,0,0,0,100,100,0,0,1,1,0,8,25,25,92,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    label = "ROADSTER / FUTURE 03" + (" · 이미지 편집 시안" if preview else "")
    events = [f"Dialogue: 0,0:00:00.00,0:01:00.00,Label,,0,0,0,,{label}",
              f"Dialogue: 0,0:00:00.00,0:01:00.00,Notice,,0,0,0,,{ass_text(project['disclosure'])}"]
    for scene in project["scenes"]:
        times = f"{ass_time(scene['start'])},{ass_time(scene['end'])}"
        events += [f"Dialogue: 1,{times},Main,,0,0,0,,{ass_text(scene['title'])}",
                   f"Dialogue: 1,{times},Caption,,0,0,0,,{ass_text(scene['caption'])}"]
    (directory / "overlay.ass").write_text(header + "\n".join(events) + "\n", encoding="utf-8")


def render(project, preview=True):
    for executable in ("ffmpeg", "ffprobe"):
        if not shutil.which(executable):
            raise ValueError(f"Install {executable} and add it to PATH. See README.md.")
    # Validate every final clip before doing any encoding work.
    if not preview:
        for scene in project["scenes"]:
            clip = OUTPUT / "clips" / f"scene_{scene['id']:02}.mp4"
            if not clip.is_file():
                raise ValueError(f"Missing generated clip: {clip.name}. Use preview for an image storyboard.")
            metadata = json.loads(run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", str(clip)]))
            if not any(stream["codec_type"] == "video" for stream in metadata["streams"]):
                raise ValueError(f"No video stream: {clip.name}")
            if float(metadata["format"]["duration"]) + 0.05 < scene["end"] - scene["start"]:
                raise ValueError(f"Clip is shorter than its planned edit: {clip.name}")
    export_plan(project)
    directory = OUTPUT / ("preview_work" if preview else "edit_work")
    directory.mkdir(exist_ok=True)
    for scene in project["scenes"]:
        seconds = scene["end"] - scene["start"]
        input_path = ROOT / project["references"][scene["reference"]] if preview else OUTPUT / "clips" / f"scene_{scene['id']:02}.mp4"
        command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
        command += ["-i", str(input_path)]
        scale = "scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,setsar=1"
        if preview:
            # Oversample before zooming to avoid visible one-pixel stepping.
            scale = ("scale=1440:2560:force_original_aspect_ratio=increase,crop=1440:2560,"
                     f"zoompan=z='1+0.035*on/{seconds * FPS}':x='iw/2-iw/zoom/2':"
                     f"y='ih/2-ih/zoom/2':d={seconds * FPS}:s=720x1280:fps={FPS},setsar=1")
        command += ["-vf", scale, "-t", str(seconds), "-an", "-r", str(FPS), "-c:v", "libx264",
                    "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p", "-threads", "2",
                    str(directory / f"scene_{scene['id']:02}.mp4")]
        print(f"Rendering scene {scene['id']:02}/10", flush=True)
        run(command)
    (directory / "concat.txt").write_text("\n".join(f"file 'scene_{s['id']:02}.mp4'" for s in project["scenes"]), encoding="utf-8")
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(directory / "concat.txt"),
         "-c", "copy", str(directory / "joined.mp4")])
    write_overlay(project, directory, preview)
    destination = OUTPUT / "final"
    destination.mkdir(exist_ok=True)
    name = "roadster_storyboard.mp4" if preview else "roadster_ai_silent.mp4"
    # Use a relative ASS path from cwd; avoids escaping Windows drive letters in filters.
    result = subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", "joined.mp4",
        "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-vf",
        "drawbox=x=0:y=0:w=iw:h=135:color=black@0.60:t=fill,"
        "drawbox=x=0:y=1010:w=iw:h=270:color=black@0.72:t=fill,ass=overlay.ass",
        "-map", "0:v:0", "-map", "1:a:0", "-t", "60", "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-pix_fmt", "yuv420p", "-threads", "2", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
        str(destination / name),
    ], cwd=directory, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode:
        raise RuntimeError(f"Subtitle render failed:\n{result.stderr[-2500:]}")
    print(f"Saved {destination / name} (silent; narration and music are not included)")

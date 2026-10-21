"""Render the 30-second Korean first film using reviewed clips and original diagrams.

Offline only. Never imports or calls the generation client.
"""
import json
import math
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from .project import ROOT, OUTPUT

W, H, FPS = 720, 1280, 24
BG, WHITE, MUTED = "#09121c", "#f3f6f8", "#aabcc9"
TEAL, ORANGE, RED = "#91f6dc", "#ffbd85", "#ff7784"
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"


def font(size, bold=False):
    return ImageFont.truetype(BOLD if bold else FONT, size, index=1)


FONTS = {size: font(size) for size in (20, 22, 24, 26, 28, 30, 34, 36, 40)}
FONTS_B = {size: font(size, True) for size in (26, 30, 34, 40, 44, 48, 54, 60, 66)}


def text(draw, xy, value, size=30, color=WHITE, bold=False, anchor=None):
    face = (FONTS_B if bold else FONTS)[size]
    draw.text(xy, value, font=face, fill=color, anchor=anchor, spacing=12)


def car(draw, cx, cy, tilt=0, color=WHITE):
    """Deliberately schematic side profile, unrelated to a claimed real design."""
    points = [(-125, 0), (-112, -35), (-60, -45), (-20, -77), (60, -77),
              (92, -42), (132, -25), (140, 0)]
    def transform(x, y):
        return cx + x * math.cos(tilt) - y * math.sin(tilt), cy + x * math.sin(tilt) + y * math.cos(tilt)
    draw.polygon([transform(x, y) for x, y in points], fill=color)
    draw.polygon([transform(x, y) for x, y in [(-42, -45), (-10, -68), (53, -68), (74, -45)]], fill=BG)
    for x in (-82, 86):
        wx, wy = transform(x, 0)
        draw.ellipse((wx-24, wy-24, wx+24, wy+24), fill=BG, outline=TEAL, width=4)


def arrow(draw, x, y1, y2, color=TEAL, width=6):
    draw.line((x, y1, x, y2), fill=color, width=width)
    sign = 1 if y2 > y1 else -1
    draw.polygon([(x, y2), (x-13, y2-sign*20), (x+13, y2-sign*20)], fill=color)


def diagram(kind, local, duration):
    frame = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(frame)
    for x in range(40, 681, 40):
        d.line((x, 340, x, 900), fill="#13232f")
    for y in range(340, 901, 40):
        d.line((40, y, 680, y), fill="#13232f")
    p = min(1, local / duration)
    if kind == "descent":
        text(d, (52, 190), "01  먼저, 천천히", 48, bold=True)
        text(d, (52, 270), "접지 전 하강 속도를 줄이기", 28, MUTED)
        car(d, 340, 560 + 160*(1-(1-p)**2))
        d.line((80, 820, 630, 820), fill=MUTED, width=4)
        arrow(d, 540, 540+120*p, 760, ORANGE)
        text(d, (90, 860), "하강 속도 ↓", 34, TEAL, True)
    elif kind == "impulse":
        text(d, (52, 190), "02  멈추는 시간을", 48, bold=True)
        text(d, (52, 255), "조금 더 길게", 48, TEAL, True)
        text(d, (52, 340), "같은 질량 · 같은 속도 변화", 26, MUTED)
        d.rounded_rectangle((52, 410, 640, 865), radius=24, fill="#102330")
        text(d, (90, 450), "짧게 멈춤", 30, RED, True)
        text(d, (380, 450), "길게 멈춤", 30, TEAL, True)
        for x in (90, 380):
            d.line((x, 540, x, 770, x+220, 770), fill=MUTED, width=3)
            text(d, (x, 508), "힘", 22, MUTED)
            text(d, (x+172, 834), "시간", 22, MUTED)
        # Same triangle area visualizes equal impulse; no measured car data.
        d.polygon([(125, 769), (165, 549), (205, 769)], fill=RED)
        d.polygon([(389, 769), (489, 681), (589, 769)], fill=TEAL)
        text(d, (96, 790), "큰 평균 힘", 24, RED)
        text(d, (385, 790), "작은 평균 힘", 24, TEAL)
        text(d, (60, 900), "평균 알짜힘 비교 · 수치 없는 개념도", 22, MUTED)
    elif kind == "suspension":
        text(d, (52, 190), "03  충격을 받아내고", 44, bold=True)
        text(d, (52, 255), "다시 튀는 힘을 줄이기", 40, TEAL, True)
        compression = 35 * max(0, math.sin(local*2.5)) * math.exp(-local*.5)
        top = 480 + compression
        d.rounded_rectangle((130, top-22, 590, top+22), radius=12, fill=WHITE)
        d.line((130, 780, 600, 780), fill=MUTED, width=6)
        # Schematic spring.
        points = [(245, top+25)]
        for n in range(13):
            points.append((245 + (28 if n % 2 else -28), top+45+(690-top-45)*n/12))
        points.append((245, 780))
        d.line(points, fill=TEAL, width=6)
        # Schematic damper.
        d.line((470, top+22, 470, 570), fill=ORANGE, width=8)
        d.rounded_rectangle((446, 560, 494, 700), radius=8, fill="#473b36", outline=ORANGE, width=4)
        d.line((470, 700, 470, 780), fill=ORANGE, width=8)
        text(d, (180, 820), "스프링", 30, TEAL, True)
        text(d, (420, 820), "댐퍼", 30, ORANGE, True)
        text(d, (78, 900), "에너지 저장 + 소산 → 튀어 오름 완화", 26, MUTED)
    elif kind == "balance":
        text(d, (52, 190), "04  균형까지", 48, bold=True)
        text(d, (52, 270), "자세와 지면을 함께 살피기", 28, MUTED)
        car(d, 340, 686, tilt=.08*math.sin(local*2)*math.exp(-local))
        d.line((110, 710, 610, 710), fill=TEAL, width=5)
        for x in (258, 426):
            d.ellipse((x-10, 700, x+10, 720), fill=ORANGE)
        arrow(d, 340, 430, 510, ORANGE)
        text(d, (120, 790), "기울기 · 접지 · 지면 상태", 30, TEAL, True)
        text(d, (82, 900), "실제 안전성은 별도의 설계와 검증 필요", 24, MUTED)
    return frame


class VideoReader:
    def __init__(self, path, start):
        self.process = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", str(start),
            "-i", str(path), "-vf", f"fps={FPS},scale={W}:{H}",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-threads", "1", "pipe:1"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    def frame(self):
        size = W*H*3
        data = self.process.stdout.read(size)
        if len(data) != size:
            raise ValueError("Source clip ended before selected range.")
        return Image.frombytes("RGB", (W, H), data)

    def close(self):
        self.process.stdout.close()
        self.process.terminate()
        self.process.wait()


def srt_time(t):
    ms = round(t*1000)
    return f"{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}"


def main():
    film = json.loads((ROOT / "config/first-film.json").read_text())
    out = OUTPUT / "first-film"
    out.mkdir(parents=True, exist_ok=True)
    narration = out / "audio/narration.wav"
    if not narration.is_file():
        raise ValueError("Run python -m shorts.narrate first.")
    captions = "\n\n".join(f"{n+1}\n{srt_time(a)} --> {srt_time(b)}\n{v}"
                              for n, (a,b,v) in enumerate(film["captions"])) + "\n"
    (out / "captions.srt").write_text(captions, encoding="utf-8")
    coast = ImageOps.fit(Image.open(ROOT / "황혼의 해안도로를 달리는 미래형 슈퍼카.png").convert("RGB"), (W, H))
    command = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
               "-s", f"{W}x{H}", "-r", str(FPS), "-i", "pipe:0", "-i", str(narration),
               "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "fast",
               "-crf", "19", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
               "-ar", "48000", "-movflags", "+faststart", "-t", "30",
               str(out / "roadster_landing_v1.mp4")]
    encoder = subprocess.Popen(command, stdin=subprocess.PIPE)
    reader, active = None, None
    # Static translucent bands keep text legible against bright footage.
    bands = Image.new("RGBA", (W, H))
    bd = ImageDraw.Draw(bands)
    for y in range(0, 340):
        alpha = round(230*(1-y/340))
        bd.line((0,y,W,y), fill=(5,12,20,alpha))
    bd.rectangle((0, 964, W, H), fill=(5,12,20,220))
    try:
        for frame_number in range(30*FPS):
            t = frame_number/FPS
            index = next(i for i,s in enumerate(film["edit"]) if s["start"] <= t < s["end"])
            scene = film["edit"][index]
            if index != active:
                if reader:
                    reader.close()
                reader = None
                if scene["kind"] == "video":
                    reader = VideoReader(OUTPUT / f"pilot-tests/clips/scene_{scene['test']:02}.mp4", scene["source_start"])
                active = index
            local = t-scene["start"]
            photographic = scene["kind"] in ("video", "coast_image")
            frame = (reader.frame() if reader else coast.copy()) if photographic else diagram(scene["kind"], local, scene["end"]-scene["start"])
            frame = Image.alpha_composite(frame.convert("RGBA"), bands).convert("RGB")
            d = ImageDraw.Draw(frame)
            text(d, (52, 65), "미래 이동 노트", 24, TEAL)
            text(d, (614, 69), "001", 22, MUTED, anchor="ra")
            d.line((52, 112, 616, 112), fill="#39515c", width=2)
            text(d, (52, 132), film["disclosure"], 22, ORANGE)
            if photographic:
                if t < 3.1:
                    text(d, (52, 195), "날아오른 다음은?", 54, bold=True)
                    text(d, (52, 280), "안전한 착지의 조건", 34, TEAL, True)
                elif t < 6.8:
                    text(d, (52, 205), "상상은 영상으로,", 44, bold=True)
                    text(d, (52, 270), "설명은 원리로.", 44, TEAL, True)
                elif t < 8.8:
                    text(d, (52, 205), "내려오는 속도부터", 44, bold=True)
                    text(d, (52, 870), "하강 연출 · 실제 접지 미확인", 24, ORANGE)
                else:
                    text(d, (52, 200), "충격 + 균형", 60, bold=True)
                    text(d, (52, 290), "여러분의 선택은?", 34, TEAL, True)
                    d.rounded_rectangle((52, 815, 350, 885), radius=30, fill="#102c32", outline=TEAL, width=2)
                    text(d, (80, 828), "타고 싶다  /  아직은!", 24, TEAL)
            else:
                text(d, (52, 70), "", 24)
                text(d, (52, 930), "설명용 도식 · 실제 차량 구조 아님", 20, ORANGE)
            caption = next(v for a,b,v in film["captions"] if a <= t < b)
            for n, line in enumerate(caption.split("\n")):
                # Captions stay within the central safe area for vertical feeds.
                bbox = d.textbbox((0,0), line, font=FONTS_B[34])
                if bbox[2] > 590:
                    raise ValueError("Caption exceeds safe width; edit line breaks.")
                text(d, (340, 1000+n*54), line, 34, WHITE, True, anchor="mt")
            d.line((52, 1140, 616, 1140), fill="#31414e", width=4)
            d.line((52, 1140, 52+564*t/30, 1140), fill=TEAL, width=4)
            text(d, (52, 1170), "AI 영상 · 한국어 합성 음성", 20, MUTED)
            if frame_number in (24, 120, 240, 312, 432, 552, 660):
                frame.save(out / f"review_{frame_number:03}.jpg", quality=94)
            encoder.stdin.write(frame.tobytes())
        encoder.stdin.close()
        if encoder.wait():
            raise RuntimeError("FFmpeg encoding failed")
    finally:
        if reader:
            reader.close()
        if encoder.poll() is None:
            encoder.terminate()
            encoder.wait()
    print(str(out / "roadster_landing_v1.mp4"))


if __name__ == "__main__":
    main()

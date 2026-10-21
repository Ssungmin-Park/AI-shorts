"""YouTube revision: moving footage, concise mechanism graphics, no fixed disclosures.

--preview exports the first 25 seconds; it uses the approved male voice when
available. Final render requires voice and CTA assets; never substitutes
a different image or silently reuses the previous female narration.
"""
import argparse
import json
import math
import subprocess

from PIL import Image, ImageDraw, ImageOps

from .first_film import W, H, FPS, BG, WHITE, TEAL, MUTED, VideoReader, text, arrow, srt_time
from .project import ROOT, OUTPUT

CONFIG = ROOT / "config/first-film-v2.json"
DEST = OUTPUT / "first-film-v2"


def caption_for(t):
    rows = [
        (0, 3, "날아오른 로드스터,\n내려올 땐 뭘 쓸까요?"),
        (3, 6.8, "테슬라가 공개한 건\n냉가스 추진기와 흡착 시스템."),
        (6.8, 9.4, "불꽃 대신 압축 공기를\n아래로 뿜어,"),
        (9.4, 11.8, "하강에 브레이크를\n거는 거죠."),
        (11.8, 15, "남은 충격은\n서스펜션이 받아주고요."),
        (15, 17.2, "팬은 역할이 달라요."),
        (17.2, 20, "차 밑 공기를 빼서\n바닥에 붙는 힘을 만듭니다."),
        (20, 22.8, "공중에서 땅을 끌어당기는\n장치는 아니에요."),
        (22.8, 25, "추진기와 팬,\n역할이 다르죠."),
        (25, 27, "여러분은 어떤가요?"),
        (27, 30, "아직 무섭다,\n아니면 타보고 싶다?")]
    return next((a,b,c) for a,b,c in rows if a <= t < b)


def base():
    frame = Image.new("RGB", (W,H), BG)
    d = ImageDraw.Draw(frame)
    # Moving gradients are supplied by the flow graphics, not a lecture grid.
    for y in range(210, 980):
        v = max(0, 1-abs(y-600)/400)
        d.line((0,y,W,y), fill=(9, int(18+10*v), int(28+16*v)))
    return frame


def thrusters(t):
    frame = base(); d = ImageDraw.Draw(frame)
    text(d,(52,100),"공중의 브레이크는?",44,bold=True)
    text(d,(52,178),"냉가스 추진기",34,TEAL,True)
    # Tank/nozzle illustration, not a drawing of Tesla's internal layout.
    bob = 10*math.sin(t*.8)
    d.rounded_rectangle((170,350+bob,510,485+bob),radius=65,fill="#253a48",outline=WHITE,width=3)
    text(d,(340,392+bob),"압축 공기",30,WHITE,True,anchor="mt")
    d.line((340,485+bob,340,570+bob),fill=TEAL,width=10)
    d.polygon([(305,560+bob),(375,560+bob),(400,620+bob),(280,620+bob)],fill="#4a6673")
    for n in range(18):
        p = (t*1.5+n/18)%1
        x = 340 + math.sin(n*2.4)*(12+p*40)
        y = 625+bob+p*225
        radius = 2+5*p
        d.ellipse((x-radius,y-radius,x+radius,y+radius),fill=TEAL)
    arrow(d,535,610,455,TEAL)
    text(d,(455,650),"위로 받는 힘",22,TEAL)
    text(d,(220,865),"공기는 아래로 ↓",28,MUTED)
    return frame


def suspension(t):
    frame=base(); d=ImageDraw.Draw(frame)
    text(d,(52,100),"남은 충격은?",44,bold=True)
    text(d,(52,178),"서스펜션이 받아줍니다",30,TEAL,True)
    comp=55*math.exp(-t*.9)*abs(math.sin(t*3))
    top=430+comp
    d.rounded_rectangle((110,top,610,top+45),radius=14,fill=WHITE)
    points=[(260,top+45)]
    for n in range(13):points.append((260+(30 if n%2 else -30),top+65+(700-top-65)*n/12))
    points.append((260,780));d.line(points,fill=TEAL,width=6)
    d.line((460,top+45,460,570),fill=TEAL,width=8)
    d.rounded_rectangle((437,560,483,700),radius=8,fill="#253a48",outline=TEAL,width=3)
    d.line((460,700,460,780),fill=TEAL,width=8)
    d.line((100,780,620,780),fill=MUTED,width=5)
    return frame


def fan(t, comparison=False):
    frame=base();d=ImageDraw.Draw(frame)
    text(d,(52,100),"팬은, 다른 일을 합니다",40,bold=True)
    text(d,(52,178),"공중 부양이 아니라 접지",30,TEAL,True)
    shift=12*math.sin(t*.7)
    left,right=115+shift,605+shift
    d.rounded_rectangle((left,435,right,505),radius=18,fill="#253a48",outline=WHITE,width=3)
    d.line((65,740,650,740),fill="#7c98a5",width=4)
    # A moving underbody module + rolling wheels, rather than a frozen car photo.
    for x in (left+55,right-55):
        d.ellipse((x-40,660,x+40,740),fill=BG,outline=MUTED,width=5)
        angle=t*3.5
        for n in range(5):
            a=angle+n*math.tau/5
            d.line((x,700,x+31*math.cos(a),700+31*math.sin(a)),fill=MUTED,width=3)
    for x in (260+shift,460+shift):
        d.ellipse((x-65,500,x+65,630),fill="#102d35",outline=TEAL,width=3)
        for n in range(5):
            a=t*7+n*math.tau/5
            d.line((x,565,x+52*math.cos(a),565+52*math.sin(a)),fill=TEAL,width=9)
    for n in range(22):
        p=(t*.7+n/22)%1
        side=-1 if n%2 else 1
        x=360+shift+side*(250*(1-p)+20)
        y=700-120*p
        d.ellipse((x-3,y-3,x+3,y+3),fill=TEAL)
    for n in range(9):
        x=((n*95-t*110)%850)-65
        d.line((x,780,x+45,780),fill="#283c4b",width=4)
    arrow(d,360+shift,310,405,TEAL)
    text(d,(170,845),"차 밑의 압력을 낮춰 접지력 ↑",26,TEAL)
    if comparison:
        d.rounded_rectangle((60,250,650,308),radius=20,fill="#19323d")
        text(d,(86,260),"공중 = 추진기   /   지면 가까이 = 팬",24,WHITE)
    return frame


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview",action="store_true")
    args=parser.parse_args()
    film=json.loads(CONFIG.read_text())
    duration=25 if args.preview else 30
    voice=DEST/"audio/narration.wav"
    asset=ROOT/film["cta_asset"]
    if not args.preview and (not voice.is_file() or not asset.is_file()):
        raise ValueError("Final render needs approved male narration and the original second attachment; use --preview meanwhile.")
    DEST.mkdir(parents=True,exist_ok=True)
    image=Image.open(asset).convert("RGB") if asset.is_file() else None
    path=DEST/("picture_preview_25s.mp4" if args.preview else "roadster_landing_v2.mp4")
    command=["ffmpeg","-y","-v","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","pipe:0"]
    if voice.is_file():command += ["-i",str(voice),"-map","0:v","-map","1:a","-c:a","aac","-b:a","192k"]
    command += ["-c:v","libx264","-preset","fast","-crf","19","-pix_fmt","yuv420p","-movflags","+faststart","-t",str(duration),str(path)]
    encoder=subprocess.Popen(command,stdin=subprocess.PIPE)
    reader=None;active=None
    try:
        for number in range(duration*FPS):
            t=number/FPS
            # Every photographic shot comes from an existing moving video.
            scene=0 if t<3 else 1 if t<6.8 else 2 if t<11.8 else 3 if t<15 else 4 if t<25 else 5
            if scene!=active:
                if reader:reader.close()
                reader=None
                if scene in (0,1):
                    test,start=(3,.25) if scene==0 else (2,.5)
                    reader=VideoReader(OUTPUT/f"pilot-tests/clips/scene_{test:02}.mp4",start)
                active=scene
            if reader:
                frame=reader.frame()
                overlay=Image.new("RGBA",(W,H));od=ImageDraw.Draw(overlay)
                for y in range(310):od.line((0,y,W,y),fill=(4,10,17,round(210*(1-y/310))))
                frame=Image.alpha_composite(frame.convert("RGBA"),overlay).convert("RGB")
                d=ImageDraw.Draw(frame)
                text(d,(52,100),"내려올 땐, 뭘 쓸까?",44,bold=True)
                if scene==1:text(d,(52,180),"테슬라가 공개한 두 장치",30,TEAL,True)
            elif scene==2:frame=thrusters(t-6.8)
            elif scene==3:frame=suspension(t-11.8)
            elif scene==4:frame=fan(t-15,comparison=t>=20)
            else:
                frame=base();d=ImageDraw.Draw(frame)
                text(d,(52,100),"여러분의 선택은?",44,bold=True)
                scale=1+.02*math.sin((t-25)*1.3)
                fitted=ImageOps.contain(image,(round(640*scale),round(430*scale)))
                frame.paste(fitted,((W-fitted.width)//2,450+(430-fitted.height)//2))
            overlay=Image.new("RGBA",(W,H));od=ImageDraw.Draw(overlay)
            od.rectangle((0,965,W,H),fill=(5,12,20,225))
            frame=Image.alpha_composite(frame.convert("RGBA"),overlay).convert("RGB")
            d=ImageDraw.Draw(frame)
            a,b,caption=caption_for(t)
            for n,line in enumerate(caption.split("\n")):
                text(d,(340,1000+n*54),line,34,WHITE,True,anchor="mt")
            if number in (24,120,240,336,432,552,660):frame.save(DEST/f"review_{number:03}.jpg",quality=94)
            encoder.stdin.write(frame.tobytes())
        encoder.stdin.close()
        if encoder.wait():raise RuntimeError("FFmpeg failed")
    finally:
        if reader:reader.close()
        if encoder.poll() is None:encoder.terminate();encoder.wait()
    rows=[];t=0
    while t<duration:
        a,b,c=caption_for(t);rows.append(f"{len(rows)+1}\n{srt_time(a)} --> {srt_time(min(b,duration))}\n{c}");t=b
    (DEST/"captions.srt").write_text("\n\n".join(rows)+"\n")
    print(str(path))


if __name__=="__main__":main()

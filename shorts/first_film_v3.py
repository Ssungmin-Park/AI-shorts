"""22-second curiosity edit. Local editing only; no generation/API imports."""
import hashlib
import json
import math
import subprocess

from PIL import Image, ImageDraw, ImageOps

from .first_film import W, H, FPS, BG, WHITE, TEAL, FONTS_B, VideoReader, text, arrow, srt_time
from .project import ROOT, OUTPUT, atomic_json

DEST=OUTPUT/"first-film-v3"


def fit_audio(film):
    import numpy as np
    import soundfile as sf
    source=ROOT/film["audio_source"]
    if hashlib.sha256(source.read_bytes()).hexdigest()!=film["audio_source_sha256"]:
        raise ValueError("Voice source changed; review edit points before continuing.")
    directory=DEST/"audio";directory.mkdir(parents=True,exist_ok=True)
    track=np.zeros(48000*film["duration"],dtype=np.float32);report=[]
    for n,line in enumerate(film["narration"]):
        a,b=line["source_start"],line["source_end"]
        available=line["end"]-line["start"]-.16
        tempo=max(1,(b-a)/available)
        if tempo>1.20:raise ValueError("Edit would rush speech; adjust timing instead.")
        seconds=(b-a)/tempo
        path=directory/f"line_{n:02}.wav"
        subprocess.run(["ffmpeg","-y","-v","error","-i",str(source),"-af",
            f"atrim=start={a}:end={b},asetpts=PTS-STARTPTS,atempo={tempo:.8f},afade=t=in:d=0.01,afade=t=out:st={seconds-.015:.8f}:d=0.015",
            "-ar","48000",str(path)],check=True)
        samples,rate=sf.read(path,dtype="float32")
        start=round((line["start"]+.06)*rate)
        if start+len(samples)>round(line["end"]*rate):raise ValueError("Speech crosses its boundary.")
        track[start:start+len(samples)]=samples
        report.append({"line":n,"source_start":a,"source_end":b,"start":line["start"]+.06,"seconds":len(samples)/rate,"tempo":tempo})
    sf.write(directory/"narration_raw.wav",track,48000)
    subprocess.run(["ffmpeg","-y","-v","error","-i",str(directory/"narration_raw.wav"),"-af",
                    "loudnorm=I=-16:TP=-1.5:LRA=7","-ar","48000",str(directory/"narration.wav")],check=True)
    atomic_json(directory/"timing.json",{"reused_voice_task_id":film["voice_task_id"],"lines":report})


def motion_overlay(t):
    layer=Image.new("RGBA",(W,H));d=ImageDraw.Draw(layer)
    if 6<=t<10.9:
        # Short arrows over moving footage, no cutaway to an explanatory slide.
        for n,x in enumerate((190,360,540)):
            p=((t-6)*1.5+n*.23)%1
            y=660+160*p
            d.line((x,y,x,y+25),fill=(145,246,220,210),width=5)
        arrow(d,620,820,680,TEAL,width=4)
    elif 10.9<=t<15.9:
        # Compact fan inset leaves the real moving car visible above it.
        d.rounded_rectangle((50,740,650,915),radius=24,fill=(5,16,24,210),outline=(145,246,220,140),width=2)
        x,y=150,825
        d.ellipse((x-52,y-52,x+52,y+52),outline=TEAL,width=3)
        for n in range(5):
            a=t*6+n*math.tau/5
            d.line((x,y,x+41*math.cos(a),y+41*math.sin(a)),fill=TEAL,width=7)
        arrow(d,570,777,862,TEAL,width=4)
    return layer


def main():
    film=json.loads((ROOT/"config/first-film-v3.json").read_text())
    fit_audio(film)
    artwork=Image.open(ROOT/film["cta_asset"]).convert("RGB")
    final=DEST/"roadster_landing_v3.mp4"
    encoder=subprocess.Popen(["ffmpeg","-y","-v","error","-f","rawvideo","-pix_fmt","rgb24",
        "-s",f"{W}x{H}","-r",str(FPS),"-i","pipe:0","-i",str(DEST/"audio/narration.wav"),
        "-map","0:v","-map","1:a","-c:v","libx264","-preset","fast","-crf","19",
        "-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-ar","48000","-movflags","+faststart",
        "-t",str(film["duration"]),str(final)],stdin=subprocess.PIPE)
    reader=None;active=None
    try:
        for n in range(FPS*film["duration"]):
            t=n/FPS
            shot=next((i for i,s in enumerate(film["shots"]) if s["start"]<=t<s["end"]),None)
            if shot!=active:
                if reader:reader.close()
                reader=None
                if shot is not None:
                    s=film["shots"][shot]
                    reader=VideoReader(OUTPUT/f"pilot-tests/clips/scene_{s['test']:02}.mp4",s["source_start"])
                active=shot
            if reader:
                frame=reader.frame().convert("RGBA")
                shade=Image.new("RGBA",(W,H));d=ImageDraw.Draw(shade)
                for y in range(330):d.line((0,y,W,y),fill=(4,10,17,round(230*(1-y/330))))
                frame=Image.alpha_composite(frame,shade)
                frame=Image.alpha_composite(frame,motion_overlay(t)).convert("RGB")
            else:
                frame=Image.new("RGB",(W,H),BG)
                scale=1+.02*math.sin((t-17.8)*1.7)
                image=ImageOps.contain(artwork,(round(660*scale),round(450*scale)))
                frame.paste(image,((W-image.width)//2,450+(450-image.height)//2))
            d=ImageDraw.Draw(frame)
            if t<3:
                text(d,(52,85),"밑에 달린 팬이",48,bold=True)
                text(d,(52,155),"잡아줄까?",66,TEAL,True)
            elif t<6:
                text(d,(52,85),"공중에서는,",44,bold=True)
                text(d,(52,153),"팬이 답이 아닙니다",40,TEAL,True)
            elif t<10.9:
                text(d,(52,85),"공중의 브레이크",44,bold=True)
                text(d,(52,153),"압축 공기를 아래로",30,TEAL,True)
            elif t<15.9:
                text(d,(52,85),"그럼, 팬은?",48,bold=True)
                text(d,(255,775),"지면 가까이에서",26,TEAL,True)
                text(d,(255,827),"붙잡는 힘",34,WHITE,True)
            elif t<17.8:
                text(d,(52,85),"공중은 추진기",44,bold=True)
                text(d,(52,153),"지면 가까이에서는 팬",34,TEAL,True)
            else:
                text(d,(52,100),"이래도, 타보고 싶나요?",40,bold=True)
            shade=Image.new("RGBA",(W,H));d=ImageDraw.Draw(shade)
            d.rectangle((0,965,W,H),fill=(5,12,20,220))
            frame=Image.alpha_composite(frame.convert("RGBA"),shade).convert("RGB");d=ImageDraw.Draw(frame)
            caption=next(c for a,b,c in film["captions"] if a<=t<b)
            for row,line in enumerate(caption.split("\n")):
                if d.textbbox((0,0),line,font=FONTS_B[34])[2]>610:raise ValueError("Caption exceeds safe area.")
                text(d,(340,1000+54*row),line,34,WHITE,True,anchor="mt")
            if n in (24,96,168,240,288,348,396,480):frame.save(DEST/f"review_{n:03}.jpg",quality=94)
            encoder.stdin.write(frame.tobytes())
        encoder.stdin.close()
        if encoder.wait():raise RuntimeError("Render failed")
    finally:
        if reader:reader.close()
        if encoder.poll() is None:encoder.terminate();encoder.wait()
    srt="\n\n".join(f"{i+1}\n{srt_time(a)} --> {srt_time(b)}\n{c}" for i,(a,b,c) in enumerate(film["captions"]))
    (DEST/"captions.srt").write_text(srt+"\n")
    print(str(final))


if __name__=="__main__":main()

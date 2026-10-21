"""Render the varied-shot/music revision from approved, saved assets only."""
import json
import math
import subprocess

from PIL import Image,ImageDraw,ImageOps

from .first_film import W,H,FPS,BG,WHITE,TEAL,FONTS_B,VideoReader,text,srt_time
from .project import ROOT,OUTPUT

DEST=OUTPUT/"first-film-v4"


def prepare_clip(name,duration):
    source=DEST/"clips"/(name+".mp4")
    output=DEST/"edit-clips"/(name+".mp4")
    output.parent.mkdir(parents=True,exist_ok=True)
    # Modest local slow motion keeps each fresh angle on screen once. Optical
    # interpolation is editing, not another paid generation; review for artifacts.
    start, usable = (1.55, 1.45) if name == "underbody_fan" else (0, 3)
    factor=duration/usable
    subprocess.run(["ffmpeg","-y","-v","error","-ss",str(start),"-t",str(usable),"-i",str(source),"-vf",
        f"setpts={factor:.8f}*(PTS-STARTPTS),minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:vsbmc=1,tpad=stop_mode=clone:stop_duration=0.2",
        "-t",str(duration+.10),"-an","-c:v","libx264","-preset","fast","-crf","18","-pix_fmt","yuv420p",str(output)],check=True)
    return output


def main():
    state=json.loads((ROOT/"docs/revision-v4-state.json").read_text())
    if any(j["status"]!="SUCCEEDED" or not j.get("file") for j in state["jobs"].values()):
        raise ValueError("Finish retrieving existing approved jobs before rendering; never submit from render.")
    film=json.loads((ROOT/"config/first-film-v3.json").read_text())
    music=DEST/"audio/voice_and_score.wav"
    if not music.is_file():raise ValueError("Prepare the original score locally first.")
    clips={name:prepare_clip(name,duration) for name,duration in [
        ("wide_descent",3.8),("rear_nozzle",4.9),("underbody_fan",3.5),("wheel_contact",3.4)]}
    shots=[(0,3.8,clips["wide_descent"],0),(3.8,6,OUTPUT/"pilot-tests/clips/scene_02.mp4",.5),
           (6,10.9,clips["rear_nozzle"],0),(10.9,14.4,clips["underbody_fan"],0),(14.4,17.8,clips["wheel_contact"],0)]
    artwork=Image.open(ROOT/film["cta_asset"]).convert("RGB")
    path=DEST/"roadster_landing_v4.mp4"
    encoder=subprocess.Popen(["ffmpeg","-y","-v","error","-f","rawvideo","-pix_fmt","rgb24",
        "-s",f"{W}x{H}","-r",str(FPS),"-i","pipe:0","-i",str(music),"-map","0:v","-map","1:a",
        "-c:v","libx264","-preset","fast","-crf","19","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k",
        "-ar","48000","-movflags","+faststart","-t","22",str(path)],stdin=subprocess.PIPE)
    reader=None;active=None
    try:
        for n in range(22*FPS):
            t=n/FPS
            shot=next((i for i,s in enumerate(shots) if s[0]<=t<s[1]),None)
            if shot!=active:
                if reader:reader.close()
                reader=None
                if shot is not None:reader=VideoReader(shots[shot][2],shots[shot][3])
                active=shot
            if reader:
                frame=reader.frame()
            else:
                frame=Image.new("RGB",(W,H),BG)
                scale=1+.02*math.sin((t-17.8)*1.7)
                im=ImageOps.contain(artwork,(round(660*scale),round(450*scale)))
                frame.paste(im,((W-im.width)//2,450+(450-im.height)//2))
            shade=Image.new("RGBA",(W,H));d=ImageDraw.Draw(shade)
            for y in range(310):d.line((0,y,W,y),fill=(4,10,17,round(210*(1-y/310))))
            d.rectangle((0,965,W,H),fill=(5,12,20,220))
            frame=Image.alpha_composite(frame.convert("RGBA"),shade).convert("RGB");d=ImageDraw.Draw(frame)
            if t<3:
                text(d,(52,85),"밑에 달린 팬이",48,bold=True)
                text(d,(52,155),"잡아줄까?",66,TEAL,True)
            elif t<6:
                text(d,(52,85),"공중에서는,",44,bold=True)
                text(d,(52,153),"팬이 답이 아닙니다",40,TEAL,True)
            elif t<10.9:
                text(d,(52,85),"공중의 브레이크",44,bold=True)
                text(d,(52,153),"압축 공기를 아래로",30,TEAL,True)
            elif t<14.4:
                text(d,(52,85),"그럼, 팬은?",48,bold=True)
            elif t<17.8:
                text(d,(52,85),"바닥에 붙잡는 힘",40,bold=True)
                text(d,(52,153),"추진기와 팬, 서로 다른 역할",26,TEAL,True)
            else:text(d,(52,100),"이래도, 타보고 싶나요?",40,bold=True)
            caption=next(c for a,b,c in film["captions"] if a<=t<b)
            for row,line in enumerate(caption.split("\n")):
                if d.textbbox((0,0),line,font=FONTS_B[34])[2]>610:raise ValueError("Caption exceeds safe area.")
                text(d,(340,1000+54*row),line,34,WHITE,True,anchor="mt")
            if n in (24,96,120,168,216,252,288,348,396,480):frame.save(DEST/f"review_{n:03}.jpg",quality=94)
            encoder.stdin.write(frame.tobytes())
        encoder.stdin.close()
        if encoder.wait():raise RuntimeError("Final encoding failed")
    finally:
        if reader:reader.close()
        if encoder.poll() is None:encoder.terminate();encoder.wait()
    srt="\n\n".join(f"{i+1}\n{srt_time(a)} --> {srt_time(b)}\n{c}" for i,(a,b,c) in enumerate(film["captions"]))
    (DEST/"captions.srt").write_text(srt+"\n")
    print(str(path))


if __name__=="__main__":main()

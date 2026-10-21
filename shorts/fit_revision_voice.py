"""Fit the single paid narration to reviewed edit points, locally and without API calls."""
import json
import subprocess

from .project import ROOT, OUTPUT, atomic_json

# Pauses were detected in the source and each segment checked with offline ASR.
# These ranges belong to task 85faff93-22b4-47cf-8852-977a2fba04b3 only.
SOURCE_RANGES = [(0,3.0),(3.98,7.8),(8.6,13.38),(14.2,16.82),
                 (17.0,22.04),(22.36,27.72),(28.27,31.85)]


def main():
    import soundfile as sf
    import numpy as np
    state=json.loads((ROOT/"docs/revision-v2-state.json").read_text())
    if state.get("voice_task_id")!="85faff93-22b4-47cf-8852-977a2fba04b3":
        raise ValueError("Narration source changed; review new source edit points first.")
    film=json.loads((ROOT/"config/first-film-v2.json").read_text())
    directory=OUTPUT/"first-film-v2/audio"
    track=np.zeros(48000*30,dtype=np.float32)
    report=[]
    for n,((a,b),line) in enumerate(zip(SOURCE_RANGES,film["narration"])):
        available=line["end"]-line["start"]-.20
        tempo=max(1,(b-a)/available)
        if tempo>1.15:raise ValueError("Excessive speech speed; revise edit timing, never regenerate automatically.")
        segment=directory/f"line_{n:02}.wav"
        duration=(b-a)/tempo
        subprocess.run(["ffmpeg","-y","-v","error","-i",str(directory/"voice_source.audio"),
            "-af",f"atrim=start={a}:end={b},asetpts=PTS-STARTPTS,atempo={tempo:.8f},afade=t=in:d=0.012,afade=t=out:st={duration-.02:.8f}:d=0.02",
            "-ar","48000",str(segment)],check=True)
        samples,rate=sf.read(segment,dtype="float32")
        start=round((line["start"]+.08)*rate)
        if start+len(samples)>round(line["end"]*rate):raise ValueError("Speech crosses cut boundary.")
        track[start:start+len(samples)]=samples
        report.append({"line":n,"source_start":a,"source_end":b,"edit_start":line["start"]+.08,"speech_seconds":len(samples)/rate,"tempo":tempo})
    sf.write(directory/"narration_raw.wav",track,48000)
    subprocess.run(["ffmpeg","-y","-v","error","-i",str(directory/"narration_raw.wav"),"-af","loudnorm=I=-16:TP=-1.5:LRA=7","-ar","48000",str(directory/"narration.wav")],check=True)
    atomic_json(directory/"timing.json",{"task_id":state["voice_task_id"],"lines":report})
    print(json.dumps(report,indent=2))


if __name__=="__main__":main()

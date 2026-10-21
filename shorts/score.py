"""Compose an original 22-second electronic underscore from oscillators and noise.

No downloaded samples, music API, lyrics, or imitation of a named song/artist.
"""
import json
import subprocess

from .project import OUTPUT, atomic_json


def main():
    import numpy as np
    import soundfile as sf
    rate=48000;duration=22;beat=60/104
    rng=np.random.default_rng(20261021)
    stereo=np.zeros((rate*duration,2),dtype=np.float64)
    folder=OUTPUT/"first-film-v4/audio";folder.mkdir(parents=True,exist_ok=True)

    def event(at,signal,level,pan=0):
        start=round(at*rate)
        if start>=len(stereo):return
        signal=signal[:len(stereo)-start]
        gains=np.sqrt(np.array([1-pan,1+pan])/2)
        stereo[start:start+len(signal)] += level*signal[:,None]*gains

    def tone(freq,seconds):
        t=np.arange(round(seconds*rate))/rate
        env=(1-np.exp(-t*100))*np.exp(-t*7)
        return env*(np.sin(2*np.pi*freq*t)+.2*np.sin(4*np.pi*freq*t))

    roots=[38,38,34,36]
    for n in range(int(duration/beat)+1):
        at=n*beat
        t=np.arange(round(.25*rate))/rate
        phase=2*np.pi*(49*t+85/40*(1-np.exp(-40*t)))
        kick=np.sin(phase)*np.exp(-t*23)
        if not 2.8<at<3.35:event(at,kick,.28)
        midi=roots[(n//4)%4];freq=440*2**((midi-69)/12)
        event(at+.03,tone(freq,beat*.85),.13)
        if n%4 in (1,3):
            noise=rng.normal(0,1,round(rate*.10));tt=np.arange(len(noise))/rate
            event(at,noise*np.exp(-tt*45),.025)
        for off in (0,.5):
            noise=rng.normal(0,1,round(rate*.045));tt=np.arange(len(noise))/rate
            high=np.diff(noise,prepend=noise[0])*.4
            event(at+off*beat,high*np.exp(-tt*90),.024,pan=.25 if n%2 else -.25)

    pattern=[0,7,12,15,7,12,3,10]
    for n in range(int(duration/(beat/2))):
        at=n*beat/2
        midi=roots[(n//8)%4]+24+pattern[n%8]
        signal=tone(440*2**((midi-69)/12),.45)
        event(at,signal,.035,pan=.45*np.sin(n*.8))
        event(at+.19,signal,.012,pan=-.45*np.sin(n*.8))

    # Brief soft transitions align with the hook answer and final choice.
    for at in (2.65,5.65,10.55,17.45):
        t=np.arange(round(.35*rate))/rate
        noise=rng.normal(0,1,len(t))
        smooth=np.convolve(noise,np.ones(20)/20,mode="same")
        event(at,smooth*np.sin(np.pi*t/.35)**2,.10,pan=-.2)
    t=np.arange(len(stereo))/rate
    envelope=np.minimum(1,t/.35)*np.minimum(1,(duration-t)/.85)
    # Pull the arrangement back at the moment of the answer.
    envelope *= np.where((t>=2.92)&(t<3.30),.18,1)
    stereo=np.tanh(stereo)*envelope[:,None]
    sf.write(folder/"score_raw.wav",stereo,rate)
    subprocess.run(["ffmpeg","-y","-v","error","-i",str(folder/"score_raw.wav"),
        "-af","loudnorm=I=-24:TP=-3:LRA=7","-ar","48000",str(folder/"score.wav")],check=True)
    voice=OUTPUT/"first-film-v3/audio/narration.wav"
    subprocess.run(["ffmpeg","-y","-v","error","-i",str(folder/"score.wav"),"-i",str(voice),
        "-filter_complex","[1:a]aformat=channel_layouts=stereo,asplit=2[v][sc];[0:a][sc]sidechaincompress=threshold=0.02:ratio=4:attack=12:release=220[bg];[v][bg]amix=inputs=2:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=7[out]",
        "-map","[out]","-ar","48000","-t","22",str(folder/"voice_and_score.wav")],check=True)
    preview=OUTPUT/"first-film-v4/music_audition_v3_picture.mp4"
    subprocess.run(["ffmpeg","-y","-v","error","-i",str(OUTPUT/"first-film-v3/roadster_landing_v3.mp4"),
        "-i",str(folder/"voice_and_score.wav"),"-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a","192k",
        "-movflags","+faststart","-t","22",str(preview)],check=True)
    atomic_json(folder/"score.json",{"method":"Original oscillator/noise composition; no external audio samples or API.",
        "duration":22,"bpm":104,"random_seed":20261021,"music_target_lufs":-24,"mixed_target_lufs":-16,
        "ducking":"Speech sidechain; ratio 4, 12ms attack, 220ms release.","additional_service_cost":0,
        "audition_scope":"Existing v3 picture with new music only; new shot generation not implied."})
    print(str(preview))


if __name__=="__main__":main()

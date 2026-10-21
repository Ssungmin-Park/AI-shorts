"""One approved male TTS request, separately budgeted from video generation.

No automatic submission retries. Status/download only reuse the saved task ID.
"""
import argparse
import hashlib
import json
import math
from urllib.parse import urlsplit
from urllib.request import build_opener

from .pilot_session import api, NoRedirect
from .project import ROOT, OUTPUT, atomic_json

STATE = ROOT / "docs/revision-v2-state.json"


def validate(state, request, balance):
    estimate = math.ceil(len(request["promptText"].encode("utf-16-le"))/2/50)
    if state["voice_status"] != "NOT_SUBMITTED" or state.get("voice_task_id"):
        raise ValueError("Existing or uncertain voice request; never resubmit.")
    if request != state["voice_request"] or request["model"] != "eleven_multilingual_v2":
        raise ValueError("Voice request changed since approval.")
    if estimate > state["voice_cap_credits"] or state["voice_cap_credits"] > 10:
        raise ValueError("Voice cost exceeds approved cap.")
    if balance != 925:
        raise ValueError("Unexpected balance change; stop before spending.")
    return estimate


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action",choices=["submit","status","download"])
    args=parser.parse_args()
    lock=OUTPUT/"first-film-v2/.voice-lock"
    lock.parent.mkdir(parents=True,exist_ok=True)
    lock.mkdir()
    try:
        state=json.loads(STATE.read_text())
        if args.action=="submit":
            config=json.loads((ROOT/"config/first-film-v2.json").read_text())
            request=config["speech_request"]
            balance=api("organization")["creditBalance"]
            estimate=validate(state,request,balance)
            state.update(voice_status="SUBMITTING",voice_reserved_credits=estimate,balance_before_voice=balance)
            atomic_json(STATE,state)
            result=api("text_to_speech",request)  # Single POST, no retries.
            if not result.get("id"):raise ValueError("No task ID; preserve journal and recover from dashboard.")
            state.update(voice_task_id=result["id"],voice_status="PENDING")
            atomic_json(STATE,state)
        else:
            if not state.get("voice_task_id"):raise ValueError("No known voice task ID.")
            result=api("tasks/"+state["voice_task_id"])
            state["voice_status"]=result["status"]
            atomic_json(STATE,state)
            if args.action=="download":
                if result["status"]!="SUCCEEDED" or not result.get("output"):
                    raise ValueError("Existing voice task not ready.")
                url=result["output"][0];parts=urlsplit(url)
                if parts.scheme!="https" or parts.hostname!="dnznrvs05pmza.cloudfront.net":
                    raise ValueError("Voice output host changed; inspect policy before downloading.")
                path=OUTPUT/"first-film-v2/audio/voice_source.audio"
                path.parent.mkdir(parents=True,exist_ok=True)
                temporary=path.with_suffix(".part")
                try:
                    with build_opener(NoRedirect).open(url,timeout=60) as response,temporary.open("wb") as f:
                        while block:=response.read(1024*1024):f.write(block)
                    if not temporary.stat().st_size:raise ValueError("Empty audio.")
                    temporary.replace(path)
                finally:temporary.unlink(missing_ok=True)
                balance=api("organization")["creditBalance"]
                state.update(voice_file=str(path.relative_to(ROOT)),voice_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),last_balance=balance,voice_actual_credits=state["balance_before_voice"]-balance)
                if state["voice_actual_credits"]>state["voice_cap_credits"]:
                    raise ValueError("Observed billing exceeded cap. No more generation is allowed.")
        atomic_json(STATE,state)
        print(json.dumps({k:state[k] for k in ["voice_task_id","voice_status","last_balance","voice_actual_credits"] if k in state}))
    finally:lock.rmdir()


if __name__=="__main__":
    try:main()
    except Exception as e:
        print(json.dumps({"stopped":type(e).__name__,"http_status":getattr(e,"code",None),"detail":str(e) if isinstance(e,ValueError) else "See saved journal; never resubmit blindly."}))
        raise SystemExit(1) from None

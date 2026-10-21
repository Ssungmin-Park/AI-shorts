"""Four approved Gen-4.5 three-second text-to-video requests, each once only."""
import argparse
import hashlib
import json
from datetime import datetime,timezone
from urllib.parse import urlsplit
from urllib.request import build_opener

from .pilot_session import api, NoRedirect
from .project import ROOT, OUTPUT, atomic_json

STATE=ROOT/"docs/revision-v4-state.json"
PLAN=ROOT/"config/first-film-v4-plan.json"


def validate(state,plan,name,balance):
    job=state["jobs"][name]
    if job["status"]!="NOT_SUBMITTED" or job.get("id"):
        raise ValueError("Existing or uncertain generation; reuse its ID, never resubmit.")
    if any(j["status"]=="SUBMITTING" for j in state["jobs"].values()):
        raise ValueError("Uncertain submission exists; recover the ID before continuing.")
    request=job["request"]
    if request!=plan["jobs"][name]["request"]:
        raise ValueError("Request differs from prepared approval plan.")
    if set(request)!={"model","duration","ratio","promptText"}:
        raise ValueError("Unexpected generation parameters; no format surcharges allowed.")
    if (request["model"],request["duration"],request["ratio"])!=("gen4.5",3,"720:1280"):
        raise ValueError("Only the approved three-second Gen-4.5 setting is allowed.")
    if state["video_authorized_cap"]!=144:
        raise ValueError("Missing or changed 144-credit authorization.")
    reserved=sum(j["reserved_credits"] for j in state["jobs"].values())
    if reserved+36>144 or balance!=state["starting_balance"]-reserved:
        raise ValueError("Budget/balance mismatch; stop before spending.")
    if len(request["promptText"].encode("utf-16-le"))//2>1000:
        raise ValueError("Prompt exceeds provider limit.")
    return request


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action",choices=["submit","status","download","balance"])
    parser.add_argument("--shot")
    args=parser.parse_args()
    lock=OUTPUT/"first-film-v4/.jobs-lock";lock.parent.mkdir(parents=True,exist_ok=True);lock.mkdir()
    try:
        state=json.loads(STATE.read_text());plan=json.loads(PLAN.read_text())
        if args.action=="balance":
            state["last_balance"]=api("organization")["creditBalance"]
            state["balance_checked_at"]=datetime.now(timezone.utc).isoformat()
            atomic_json(STATE,state);print(json.dumps({"creditBalance":state["last_balance"]}));return
        if args.shot not in state["jobs"]:raise ValueError("Select one prepared shot.")
        job=state["jobs"][args.shot]
        if args.action=="submit":
            balance=api("organization")["creditBalance"]
            request=validate(state,plan,args.shot,balance)
            job.update(status="SUBMITTING",reserved_credits=36,submitted_at=datetime.now(timezone.utc).isoformat())
            atomic_json(STATE,state)
            task=api("text_to_video",request)  # One POST. No retry path.
            if not task.get("id"):raise ValueError("Missing task ID; preserve SUBMITTING, inspect dashboard.")
            job.update(id=task["id"],status="PENDING")
            atomic_json(STATE,state)
        else:
            if not job.get("id"):raise ValueError("No saved ID. No generation was attempted.")
            task=api("tasks/"+job["id"]);job["status"]=task["status"]
            atomic_json(STATE,state)
            if args.action=="download":
                if task["status"]!="SUCCEEDED" or not task.get("output"):
                    raise ValueError("Existing task is not downloadable yet.")
                url=task["output"][0];parts=urlsplit(url)
                if parts.scheme!="https" or parts.hostname!="dnznrvs05pmza.cloudfront.net":
                    job["download_host"]=parts.hostname;atomic_json(STATE,state)
                    raise ValueError("Output host changed; check enforced policy before download.")
                file=OUTPUT/"first-film-v4/clips"/(args.shot+".mp4")
                file.parent.mkdir(parents=True,exist_ok=True);partial=file.with_suffix(".part")
                try:
                    with build_opener(NoRedirect).open(url,timeout=60) as response,partial.open("wb") as f:
                        while block:=response.read(1024*1024):f.write(block)
                    if not partial.stat().st_size:raise ValueError("Empty output")
                    partial.replace(file)
                finally:partial.unlink(missing_ok=True)
                job.update(file=str(file.relative_to(ROOT)),sha256=hashlib.sha256(file.read_bytes()).hexdigest(),bytes=file.stat().st_size)
                state["last_balance"]=api("organization")["creditBalance"]
                state["actual_new_video_credits"]=state["starting_balance"]-state["last_balance"]
                atomic_json(STATE,state)
        print(json.dumps({"shot":args.shot,"id":job.get("id"),"status":job["status"],"file":job.get("file"),"last_balance":state.get("last_balance")}))
    finally:lock.rmdir()


if __name__=="__main__":
    try:main()
    except Exception as e:
        print(json.dumps({"stopped":type(e).__name__,"http_status":getattr(e,"code",None),"detail":str(e) if isinstance(e,ValueError) else "Saved task journal preserved; never resubmit blindly."}))
        raise SystemExit(1) from None

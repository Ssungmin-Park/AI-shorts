"""One-shot continuation of the approved pilot; status/download never submit.

The tracked journal is authoritative. Never delete/reset SUBMITTING to retry.
API exceptions are reduced to type/status so headers and signed URLs stay private.
"""
import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .pilot import load_tests
from .project import ROOT, OUTPUT, atomic_json
from .runway import image_uri

JOURNAL = ROOT / "docs/production-state.json"


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def api(route, payload=None):
    headers = {"Authorization": "Bearer " + os.environ["RUNWAYML_API_SECRET"],
               "X-Runway-Version": "2024-11-06"}
    data = None
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode()
    with build_opener(NoRedirect).open(Request(
        "https://api.dev.runwayml.com/v1/" + route,
        headers=headers, data=data), timeout=60) as response:
        return json.load(response)


def fingerprint(request):
    return hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()


def validate_submission(state, number, request, balance):
    job = state["jobs"][str(number)]
    if number not in (2, 3) or job["status"] != "NOT_SUBMITTED" or job.get("id"):
        raise ValueError("Existing/uncertain task: submission blocked. Use status/download.")
    if job["request"] != request:
        raise ValueError("Approved settings changed; stop before spending.")
    if (request["model"], request["duration"], request["ratio"]) != ("gen4_turbo", 5, "720:1280"):
        raise ValueError("Only approved Gen-4 Turbo five-second tests are allowed.")
    if any(j["status"] == "SUBMITTING" for j in state["jobs"].values()):
        raise ValueError("Uncertain submission exists; recover its ID before continuing.")
    reserved = sum(j["reserved_credits"] for j in state["jobs"].values())
    if reserved + 25 > 75 or balance != 1000 - reserved:
        raise ValueError("Budget/balance mismatch; stop before spending.")
    if number == 3 and state["jobs"]["2"]["status"] != "SUCCEEDED":
        raise ValueError("Review test 2 before submitting test 3.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["submit", "status", "download", "balance"])
    parser.add_argument("--test", type=int, choices=[1, 2, 3])
    args = parser.parse_args()
    lock = OUTPUT / "pilot-tests/.session-lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    try:
        lock.mkdir()
    except FileExistsError:
        raise ValueError("Session is running or was interrupted; inspect the journal before recovering the lock.") from None
    try:
        run_session(args, parser)
    finally:
        lock.rmdir()


def run_session(args, parser):
    state = json.loads(JOURNAL.read_text(encoding="utf-8"))
    if args.action == "balance":
        state["last_balance"] = api("organization")["creditBalance"]
        state["balance_checked_at"] = datetime.now(timezone.utc).isoformat()
        atomic_json(JOURNAL, state)
        print(json.dumps({"creditBalance": state["last_balance"]}))
        return
    if args.test is None:
        parser.error("--test is required")
    job = state["jobs"][str(args.test)]
    if args.action == "submit":
        project, requests = load_tests()
        request = requests[args.test - 1]
        balance = api("organization")["creditBalance"]
        validate_submission(state, args.test, request, balance)
        # Prepare image before reserving; no paid retry if any later step fails.
        uri = image_uri(ROOT / request["image"])
        payload = {"model": request["model"], "duration": request["duration"],
                   "ratio": request["ratio"], "promptText": request["prompt_text"],
                   "promptImage": uri}
        job.update(status="SUBMITTING", reserved_credits=25,
                   submitted_at=datetime.now(timezone.utc).isoformat())
        atomic_json(JOURNAL, state)
        atomic_json(OUTPUT / "pilot-tests/jobs" / f"scene_{args.test:02}.json",
                    dict(job, fingerprint=fingerprint(request)))
        result = api("image_to_video", payload)  # Exactly one POST. No retries.
        if not result.get("id"):
            raise ValueError("Missing task ID; preserve SUBMITTING and check dashboard.")
        job.update(id=result["id"], status="PENDING")
    else:
        if not job.get("id"):
            raise ValueError("No known task ID. No submission was attempted.")
        result = api("tasks/" + job["id"])
        job["status"] = result["status"]
        atomic_json(JOURNAL, state)
        if args.action == "download":
            if result["status"] != "SUCCEEDED" or not result.get("output"):
                raise ValueError("Existing task is not downloadable yet.")
            url = result["output"][0]
            parts = urlsplit(url)
            if parts.scheme != "https" or parts.hostname != "dnznrvs05pmza.cloudfront.net":
                raise ValueError("Unexpected result host; inspect policy before downloading.")
            clip = OUTPUT / "pilot-tests/clips" / f"scene_{args.test:02}.mp4"
            clip.parent.mkdir(parents=True, exist_ok=True)
            partial = clip.with_suffix(".part")
            try:
                # Separate request, no API headers; redirects are not followed.
                with build_opener(NoRedirect).open(url, timeout=60) as response, partial.open("wb") as target:
                    while block := response.read(1024 * 1024):
                        target.write(block)
                if not partial.stat().st_size:
                    raise ValueError("Empty download")
                partial.replace(clip)
            finally:
                partial.unlink(missing_ok=True)
            job.update(file=str(clip.relative_to(ROOT)), bytes=clip.stat().st_size,
                       sha256=hashlib.sha256(clip.read_bytes()).hexdigest())
    atomic_json(JOURNAL, state)
    atomic_json(OUTPUT / "pilot-tests/jobs" / f"scene_{args.test:02}.json",
                dict(job, fingerprint=fingerprint(job["request"])))
    print(json.dumps({"test": args.test, "id": job.get("id"), "status": job["status"],
                      "file": job.get("file")}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(json.dumps({"stopped": type(error).__name__,
                          "http_status": error.code if isinstance(error, HTTPError) else None,
                          "detail": str(error) if isinstance(error, ValueError) else "See saved task journal; never resubmit blindly."}))
        raise SystemExit(1) from None

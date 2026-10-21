"""Three fixed five-second tests. Dry-run by default; execute one test at a time."""
import argparse
import json
import sys

from .project import OUTPUT, ROOT, atomic_json, request_for
from .runway import generate_scene


def load_tests():
    project = json.loads((ROOT / "config/pilot-tests.json").read_text(encoding="utf-8"))
    scenes = project["scenes"]
    if len(scenes) != 3 or [scene["id"] for scene in scenes] != [1, 2, 3]:
        raise ValueError("The pilot must contain exactly three tests numbered 1, 2, 3.")
    requests = []
    for scene in scenes:
        if scene["end"] - scene["start"] != 5:
            raise ValueError("Every pilot test must request exactly five seconds.")
        if len(scene["prompt"].encode("utf-16-le")) // 2 > 1000:
            raise ValueError("Test prompt exceeds the provider limit.")
        requests.append(request_for(project, scene))
    return project, requests


def main():
    parser = argparse.ArgumentParser(description="Roadster pilot: three tests, 75 planned credits total")
    parser.add_argument("--test", type=int, choices=[1, 2, 3])
    parser.add_argument("--execute", action="store_true", help="Send one request, planned cost 25 credits")
    args = parser.parse_args()
    if args.execute and args.test is None:
        parser.error("--execute requires --test 1, 2, or 3; bulk generation is disabled")
    project, requests = load_tests()
    if args.execute:
        generate_scene(project, project["scenes"][args.test - 1], execute=True,
                       output_dir=OUTPUT / "pilot-tests")
    else:
        atomic_json(OUTPUT / "pilot-tests/plan.json", requests)
        selected = requests if args.test is None else [requests[args.test - 1]]
        print(json.dumps(selected, ensure_ascii=False, indent=2))
        print("DRY RUN: no API request. 5 credits/second assumption: 25 per test, 75 total.")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError, OSError) as error:
        print(f"Stopped: {error}", file=sys.stderr)
        sys.exit(1)

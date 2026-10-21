import argparse
import sys

from .project import export_plan, load_project


def main():
    parser = argparse.ArgumentParser(description="Roadster shorts: free local preview, opt-in Runway generation")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("plan", help="Validate images and export prompts/subtitles without an API")
    commands.add_parser("preview", help="Render a free silent 60s image storyboard using FFmpeg")
    commands.add_parser("assemble", help="Trim and assemble all ten downloaded AI clips")
    generate = commands.add_parser("generate", help="Show a request; --execute sends one paid API request")
    generate.add_argument("--scene", type=int, default=1, choices=range(1, 11))
    generate.add_argument("--execute", action="store_true", help="Allow an API request that may spend credits")
    args = parser.parse_args()
    project = load_project()
    if args.command == "plan":
        export_plan(project)
    elif args.command in {"preview", "assemble"}:
        from .render import render
        render(project, preview=args.command == "preview")
    else:
        from .runway import generate_scene
        generate_scene(project, project["scenes"][args.scene - 1], execute=args.execute)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError, OSError) as error:
        print(f"Stopped: {error}", file=sys.stderr)
        sys.exit(1)

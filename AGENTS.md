# Project Rules — Blender Control (`BLENDER_CONTROL`)

## Git & GitHub Synchronization (Always On)

- **Remote Repository**: `https://github.com/markoboskoauroville/blender-control` (public, branch `main`).
- **Always Keep Local and Remote in Sync**:
  1. Before starting new work in a session, run `git status` and `git pull --rebase origin main` if remote changes exist.
  2. Whenever you create, modify, or delete skills, scripts, documentation, `.blend` project builders, or showcase outputs, stage, commit with a clear message, and push immediately to `origin main` (or run `./scripts/sync_github.sh "<commit message>"`).
  3. Never leave uncommitted or unpushed work at the end of a task.

## Blender Control Workflow

- Always consult `.agents/skills/blender-control/SKILL.md` when controlling Blender, writing `bpy` scripts, managing scenes, or rendering images/animations.
- Prefer controlling the **live open Blender GUI** via `.agents/skills/blender-control/scripts/blender_cli.py` (`127.0.0.1:9876`) when the user wants interactive visual feedback in the open Blender window, and use headless CLI mode (`/Applications/Blender.app/Contents/MacOS/Blender --background ...`) when running isolated batch jobs.

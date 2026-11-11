# Project Rules — Blender Control (`BLENDER_CONTROL`)

## Git & GitHub Synchronization (Always On)

- **Remote Repository**: `https://github.com/markoboskoauroville/blender-control` (public, branch `main`).
- **Always Keep Local and Remote in Sync**:
  1. Before starting new work in a session, run `git status` and `git pull --rebase origin main` if remote changes exist.
  2. Whenever you create, modify, or delete skills, scripts, documentation, `.blend` project builders, or showcase outputs, stage, commit with a clear message, and push immediately to `origin main` (or run `./scripts/sync_github.sh "<commit message>"`).
  3. Never leave uncommitted or unpushed work at the end of a task.

## Blender Control & Video Editing Workflow

- Always consult `.agents/skills/blender-control/SKILL.md` when controlling Blender, writing `bpy` scripts, managing scenes, or rendering images/animations.
- Always consult `.agents/skills/video-frame-precise-edit/SKILL.md` and `LESSONS.md` when performing frame-by-frame surgical video edits, text removal, or material recoloring so edge flicker, 8-bit banding, and unintended hardware recoloring never occur.
- Prefer controlling the **live open Blender GUI** via `.agents/skills/blender-control/scripts/blender_cli.py` (`127.0.0.1:9876`) when the user wants interactive visual feedback in the open Blender window, and use headless CLI mode (`/Applications/Blender.app/Contents/MacOS/Blender --background ...`) when running isolated batch jobs.
- Before resuming or closing a session, read and update `TAKEOVER.md`, `LESSONS.md`, and `manifests/handover-checkpoint.json`.
- **Cross-Project Guardrails**:
  - **WhatsApp Self-Notification**: Only message Marko's own `(You)` self-chat (`+385 97 679 0768`) via Firefox WebDriver BiDi (`/Users/markobosko/Developer/FIREFOX_CONTROL/firefoxctl`); never message third parties or hijack OS mouse/keyboard focus.
  - **GCP Free Credit Cap**: Enforce the `$285.00 USD` hard safety cap (`min-instances = 0`) on Billing Account `0193A0-F5144A-C98D4D` (`manifests/cloud-video-studio-manifest.yaml`).

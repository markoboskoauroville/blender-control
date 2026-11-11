---
name: blender-control
description: >-
  Controls the live open Blender 5.2 GUI application (via localhost TCP JSON-RPC bridge)
  or headless background Blender CLI on macOS (Apple Silicon Metal GPU). Use this skill
  whenever the user asks to create, edit, inspect, animate, or render 3D scenes, models,
  materials, simulations, mechanisms, or videos in Blender.
---

# Blender Control Skill (Live GUI + Headless CLI)

This workspace controls **Blender 5.2.1 LTS** (`/Applications/Blender.app/Contents/MacOS/Blender`, Python `3.13`, Apple M1 Pro 16-core Metal GPU) in two complementary modes:

1. **Live GUI Mode (Default & Preferred)**: Sends commands over `127.0.0.1:9876` to [blender_control_bridge.py](./scripts/blender_control_bridge.py) running inside the open `Blender.app` window. Objects, shaders, animations, and camera framing appear immediately in front of the user.
2. **Headless CLI Mode**: Runs `/Applications/Blender.app/Contents/MacOS/Blender --background` for isolated batch rendering or heavy background jobs without touching the active GUI session.

Before writing `bpy` scripts for Blender 5.2, review [blender_5_2_api_guide.md](./references/blender_5_2_api_guide.md) for critical 5.2 API changes (`Principled BSDF` socket names, Slotted Actions `channelbag`, `media_type = 'VIDEO'`, and Metal GPU setup).

---

## Step 1: Verify or Connect to the Open Blender Application

Always verify the live bridge connection first:

```bash
python3 .agents/skills/blender-control/scripts/blender_cli.py ping
```

If `ping` fails (e.g., Blender is not open yet or was started before installing the startup bridge), run the installer/connector script:

```bash
bash .agents/skills/blender-control/scripts/install_bridge.sh
```

- Copies [blender_control_bridge.py](./scripts/blender_control_bridge.py) into `~/Library/Application Support/Blender/5.2/scripts/startup/` so every GUI launch starts the bridge automatically on `127.0.0.1:9876`.
- Safely connects to or launches `Blender.app` (`open -g -a Blender`) without stealing window focus.
- If `Blender.app` already has an unsaved `.blend` file open without the bridge loaded, ask the user to click **Blender -> System -> Reload Scripts** in the macOS menu bar.

---

## Step 2: Inspect & Control the Live Scene via `blender_cli.py`

Use [blender_cli.py](./scripts/blender_cli.py) for all live operations:

```bash
# 1. Inspect current objects, cameras, materials, frame range, and render engine
python3 .agents/skills/blender-control/scripts/blender_cli.py info

# 2. Clear the live scene cleanly (removes all objects & orphan datablocks)
python3 .agents/skills/blender-control/scripts/blender_cli.py reset

# 3. Execute a scene-builder Python script live on Blender's main UI thread
python3 .agents/skills/blender-control/scripts/blender_cli.py run projects/my_scene/build.py

# 4. Execute quick inline Python expressions/snippets
python3 .agents/skills/blender-control/scripts/blender_cli.py exec "RESULT = [o.name for o in bpy.data.objects]"

# 5. Switch the user's live Blender 3D viewport to Material Preview or Rendered Camera view
python3 .agents/skills/blender-control/scripts/blender_cli.py viewport --shading MATERIAL

# 6. Save or open .blend project files in the live GUI
python3 .agents/skills/blender-control/scripts/blender_cli.py save projects/my_scene/scene.blend
python3 .agents/skills/blender-control/scripts/blender_cli.py open projects/my_scene/scene.blend
```

---

## Step 3: Render Stills, Viewport Previews & Animations

### Fast Viewport Preview (<0.2s)
Use a viewport screenshot first to verify camera framing, object placement, and clipping before running a full ray-traced render:

```bash
python3 .agents/skills/blender-control/scripts/blender_cli.py screenshot /tmp/preview.png
```
Inspect `/tmp/preview.png` with `read_file` to visually check composition and lighting!

### High-Quality Still Render (Cycles Metal GPU or EEVEE)
```bash
# Cycles with automatic Apple M1 Pro 16-core Metal GPU acceleration
python3 .agents/skills/blender-control/scripts/blender_cli.py render projects/my_scene/render.png \
  --engine CYCLES --samples 64 --width 1920 --height 1080

# Fast real-time PBR render with EEVEE
python3 .agents/skills/blender-control/scripts/blender_cli.py render projects/my_scene/render.png \
  --engine BLENDER_EEVEE --samples 32 --width 1920 --height 1080
```

### MP4 (H.264) Animation Render
```bash
python3 .agents/skills/blender-control/scripts/blender_cli.py render-anim projects/my_scene/animation.mp4 \
  --engine BLENDER_EEVEE --samples 32 --width 1280 --height 720 --start 1 --end 120 --fps 30
```

### Headless Batch Mode (Isolated Process)
When rendering heavy jobs without blocking the live GUI viewport:
```bash
python3 .agents/skills/blender-control/scripts/blender_cli.py run projects/my_scene/build.py --headless
```

---

## Step 4: Scene Construction & Validation Checklist

1. **Self-Contained Builder Scripts**: Store each project in `projects/<project_name>/build.py` so scenes are 100% reproducible and Git-friendly alongside rendered outputs and `.blend` files.
2. **Camera Aiming (`TRACK_TO` or Quaternion)**: Always point the camera reliably at a target Empty or world coordinate using `(target - cam.location).to_track_quat('-Z', 'Y')` and set `scene.camera = cam`.
3. **Three-Point / Studio Lighting & World**: Never leave a dark default grey background; configure World shader nodes + Area/Sun lights with realistic wattage (`100W`–`1500W` depending on scene scale) and `AgX` or `Filmic` color management (`scene.view_settings.view_transform = 'AgX'`, `look = 'AgX - Medium High Contrast'`).
4. **Visual Verification**: Always inspect rendered `.png` or `.mp4` outputs using `read_file` to confirm framing, exposure, materials, and motion before finishing.
5. **GitHub Sync**: After creating or updating projects/skills, run `./scripts/sync_github.sh "<commit message>"` to keep local and `origin/main` synchronized.

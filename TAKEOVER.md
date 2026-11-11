# TAKEOVER / HANDOVER: `BLENDER_CONTROL`

**Closed**: `11.11.2026`  
**Repository**: `https://github.com/markoboskoauroville/blender-control` (`main`, public, auto-synced)  
**Workspace**: `/Users/markobosko/Developer/BLENDER_CONTROL`  
**Environment**: macOS (Apple M1 Pro 16-core Metal GPU), Blender `5.2.1 LTS` (`/Applications/Blender.app`), Python `3.13.13`

---

## 1. Current State Summary

### Completed & Production-Ready
1. **Blender 5.2 Live Control Bridge & CLI (`.agents/skills/blender-control/`)**:
   - Startup daemon [`blender_control_bridge.py`](./.agents/skills/blender-control/scripts/blender_control_bridge.py) installed into `~/Library/Application Support/Blender/5.2/scripts/startup/blender_control_bridge.py` (listening on `127.0.0.1:9876`, executing safely on Blender's main UI thread every `50ms`, patched with automatic `#` filename placeholder protection).
   - Full CLI [`blender_cli.py`](./.agents/skills/blender-control/scripts/blender_cli.py) (`ping`, `info`, `reset`, `exec`, `run`, `viewport`, `screenshot`, `render`, `render-anim`, `save`, `open`, plus `--headless`).
   - Blender 5.2 API Reference [`blender_5_2_api_guide.md`](./.agents/skills/blender-control/references/blender_5_2_api_guide.md).
2. **Frame-Precise Video Editing Skill (`.agents/skills/video-frame-precise-edit/SKILL.md`)**:
   - Codifies AV1 decoding via Blender 5.2 VSE, time-locked static silhouette mattes, time-invariant surface text albedo unmixing, 3D-kinematic black hardware preservation, multiplied matte-vs-glossy reflections, and `float32` + TPDF anti-banding dithering.
3. **Three Rendered Showcase Projects**:
   - [`projects/01_glass_metal_sculpture/`](./projects/01_glass_metal_sculpture/) — Cycles Metal GPU anisotropic gold `(2,3)` torus knot & crystal glass torus.
   - [`projects/02_parametric_cyber_grid/`](./projects/02_parametric_cyber_grid/) — EEVEE `169`-prism hexagonal wave matrix.
   - [`projects/03_straight_line_mechanism/`](./projects/03_straight_line_mechanism/) — `120`-frame `H.264` Tusi couple / Cardano hypocycloid straight-line mechanism.
4. **Project 04 (`How Rotation Becomes a Straight Line`) — V1 Delivered & V2 Subpixel-Calibrated**:
   - Untouched original AV1 backup preserved at [`projects/04_how_rotation_becomes/original_reference.mp4`](./projects/04_how_rotation_becomes/original_reference.mp4) (`523,229` bytes, `720x1280` @ `30 FPS`, `393` frames, `AAC` stereo audio).
   - Croatian prompt [`changes.txt`](./changes.txt) decoded: `"Možeš li u ovom videu izbrisati tekst i zamjeniti crno u zelno i ružičasto u plavo"`.
   - V1 scripts & outputs committed (`process_frames.py`, `build_blender_vse.py`, `verify_frame_by_frame.py`, `verification_grid.png`, `How_Rotation_Becomes_a_Straight_Line_Modified.mp4`).
   - Complete 400%-zoom autopsy of V1 and exact subpixel camera/kinematic calibration recorded in [`LESSONS.md`](./LESSONS.md) and [`manifests/handover-checkpoint.json`](./manifests/handover-checkpoint.json).

---

## 2. Exact Next Steps for Immediate Resumption

### Priority 1: Render & Frame-by-Frame Verify "Version 2" (`projects/04_how_rotation_becomes/`)
Follow [`.agents/skills/video-frame-precise-edit/SKILL.md`](./.agents/skills/video-frame-precise-edit/SKILL.md) and the calibrated parameters in [`manifests/handover-checkpoint.json`](./manifests/handover-checkpoint.json):
1. **Keep All 3 Joint Hardware Assemblies 100% Black**:
   - **Back Pivot**: Matte black oxide `6-lobe` socket-head cap screw (`cx=114.5, cy=480.5, rx=25.0, ry=13.3, dh=15.0` in `f=1..182`; `cx=392.5, cy=363.0, r=29.8` in `f=213..393`; hex-tracked across `f=183..212`).
   - **Middle Joint**: Smooth chamfered flat black cap + middle cylindrical spacer + bottom nut underneath the yellow crank (`180`-frame sinusoidal harmonic trajectory, paused at `0°` during `f=182..213`).
   - **Front Slider Joint**: Matte black `6-lobe` socket-head cap screw + **mirror-glossy black cylindrical spacer** sitting on the mint-teal slider.
2. **Eliminate All Edge Flickering, Text Artifacts & Color Banding**:
   - Use **one static `float32` rail silhouette matte** for `f=1..182` and **one static `float32` rail silhouette matte** for `f=213..393` (warped smoothly across `f=183..212`) — zero per-frame binary morphology.
   - Erase `'B. Cruz'` across **all `393` frames** (including orbit `f=183..212`) via time-invariant white-ink albedo unmixing (`min(R,G,B)` separation + 1D rail-axis shading profile) instead of fixed-box Laplace inpainting.
   - Multiply matte-vs-reflective contrast: boost satin bevel rim highlights (`1.3x`) on the green rail & blue rod, preserve and enhance the mirror-glossy front black spacer reflections (rotating the reflected coral collar tint to blue while keeping the mint slider reflection!), and apply `±0.5 LSB` TPDF dithering + `scene.render.dither_intensity = 1.5`.
3. **Compare Frame by Frame Until 100% Blending**:
   - Write `How_Rotation_Becomes_a_Straight_Line_V2.mp4` and overwrite `How Rotation Becomes a Straight Line ⚙️#engineering #technology #mechanism.mp4`.
   - Inspect `400%` zoom crops and temporal derivative `|I(t+1) - I(t)|` across all `393` frames until edge flicker, banding, and text residuals are `0.00%`.

### Priority 2: Send WhatsApp Self-Message with Attached V2 Video via Firefox
- Use `/Users/markobosko/Developer/FIREFOX_CONTROL/firefoxctl` (WebDriver BiDi on Firefox, zero OS mouse/keyboard hijacking) and follow `/Users/markobosko/Developer/ELEVATE_MEDIA_MONITOR/tools/whatsapp_self.py`.
- **Safety Constraint**: Send **strictly from Marko to Marko (`(You)`, `+385 97 679 0768`)** with `How_Rotation_Becomes_a_Straight_Line_V2.mp4` attached via WhatsApp Web's `input[type="file"][accept*="video"]`. Never message any other contact or group.

### Priority 3: Provision & Deploy Google Cloud Video-Prompt Studio (`manifests/cloud-video-studio-manifest.yaml`)
- Use `gcloud` (`marko.bosko@auroville.community`, Org `87869539786`, Billing Account `0193A0-F5144A-C98D4D` with `$299.97` free credit expiring `2026-12-03` and `$285.00` hard cap shared with `/Users/markobosko/Developer/ANTIGRAVITY_OFFLOAD_TO_CLOUD`).
- Deploy the FastAPI + Vertex AI Gemini (`gemini-2.5-pro`/`flash`) + Headless Blender + FFmpeg service defined in [`manifests/cloud-video-studio-manifest.yaml`](./manifests/cloud-video-studio-manifest.yaml) to Cloud Run (`europe-west1`, `min-instances=0`) and test end-to-end by uploading `original_reference.mp4` + `changes.txt`.

---

## 3. Canonical Handover Files Index

| Category | File | Purpose |
| :--- | :--- | :--- |
| **Handover** | [`TAKEOVER.md`](./TAKEOVER.md) | Complete project state, resumption runbook, and priorities |
| **Handover (Alias)** | [`HANDOVER.md`](./HANDOVER.md) | Pointer/summary linked to `TAKEOVER.md` & `manifests/` |
| **Rules** | [`AGENTS.md`](./AGENTS.md) | Always-on Git sync, Blender GUI/CLI workflow, and cross-tool safety rules |
| **Lessons** | [`LESSONS.md`](./LESSONS.md) | Blender 5.2 API gotchas, AV1 VSE decoding, V1 pixel autopsy & V2 math |
| **Skill 1** | [`.agents/skills/blender-control/SKILL.md`](./.agents/skills/blender-control/SKILL.md) | Live Blender 5.2 GUI TCP bridge (`127.0.0.1:9876`) + headless CLI |
| **Skill 2** | [`.agents/skills/video-frame-precise-edit/SKILL.md`](./.agents/skills/video-frame-precise-edit/SKILL.md) | Zero-flicker, zero-banding surgical 3D video editing & verification |
| **Manifest 1** | [`manifests/project-manifest.yaml`](./manifests/project-manifest.yaml) | Declarative inventory of skills, projects, outputs & V2 requirements |
| **Manifest 2** | [`manifests/cloud-video-studio-manifest.yaml`](./manifests/cloud-video-studio-manifest.yaml) | GCP Cloud Run + Vertex AI + Headless Blender video-prompt platform spec |
| **Manifest 3** | [`manifests/handover-checkpoint.json`](./manifests/handover-checkpoint.json) | Machine-readable state checkpoint & calibrated 393-frame kinematics |

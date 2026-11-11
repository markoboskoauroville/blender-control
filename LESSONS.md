# LESSONS: `blender-control`

Chronological engineering lessons, API gotchas, and visual quality findings from building `BLENDER_CONTROL` on macOS (Apple M1 Pro 16-core Metal GPU, Blender `5.2.1 LTS`, Python `3.13`).

---

## 11.11.2026 — Blender 5.2.1 LTS Live Bridge & API Changes

- **Thread-Safe Live GUI Control (`127.0.0.1:9876`)**: `bpy` crashes or corrupts state if called directly from a background socket thread. Running a lightweight `ThreadingTCPServer` on a daemon thread that pushes JSON-RPC payloads onto a `queue.Queue` and drains them every `50ms` inside `bpy.app.timers` on Blender's main UI thread gives `<55ms` interactive latency with zero crashes.
- **Blender 5.2 `Principled BSDF` Socket Renames**: Legacy 3.x socket names (`'Transmission'`, `'Clearcoat'`, `'Emission'`, `'Specular'`) raise `KeyError` in Blender 5.2. Always use `'Transmission Weight'`, `'Coat Weight'`, `'Coat Roughness'`, `'Emission Color'`, `'Emission Strength'`, and `'Specular IOR Level'`.
- **Blender 5.0+ Slotted / Layered Actions**: `action.fcurves` no longer exists directly on `bpy.types.Action`. Use `bpy_extras.anim_utils.action_get_channelbag_for_slot(act, slot).fcurves` to inspect or change keyframe interpolation (`LINEAR`, `BEZIER`).
- **Blender 5.2 `media_type` & Compositor**:
  - `scene.render.image_settings.media_type` (`'IMAGE'`, `'MULTI_LAYER_IMAGE'`, `'VIDEO'`) must be set before `file_format` when switching between PNG stills and `MPEG4`/`H264` video output.
  - `scene.node_tree` was replaced by `scene.compositing_node_group` in Blender 5.0+.
- **Literal `#` in Output Filenames**: Setting `scene.render.filepath` to a filename containing `#` (such as YouTube/Shorts titles like `...⚙️#engineering #technology #mechanism.mp4`) causes Blender to interpret `#` as frame-padding digits (`1-393mechanism.mp4`). Always render to a `#`-free path first and `os.replace()` afterward (now built directly into `blender_control_bridge.py`).
- **Apple Silicon Metal GPU Setup**: Setting `prefs.compute_device_type = 'METAL'`, calling `prefs.refresh_devices()` (or `get_devices()`), enabling only `dev.type == 'METAL'`, and setting `scene.cycles.device = 'GPU'` activates all 16 GPU cores on Apple M1 Pro cleanly in both GUI and `--background` modes.

---

## 11.11.2026 — Decoding & Editing `How Rotation Becomes a Straight Line` (`projects/04_how_rotation_becomes`)

- **Non-UTF-8 Croatian Prompt (`changes.txt`)**: `changes.txt` contained GB18030/legacy byte sequences (`\x810\x976`) for Croatian diacritics (`ž`, `š`, `č`), causing standard UTF-8 text readers to reject it as binary. Raw byte inspection decoded the exact prompt:
  `"Možeš li u ovom videu izbrisati tekst i zamjeniti crno u zelno i ružičasto u plavo"` (*"Can you erase the text in this video and replace black with green and pink with blue"*).
- **AV1 Video Decoding Fallback**: System `ffmpeg` on macOS lacked an `av1` decoder (`0` frames decoded). Loading the MP4 into Blender 5.2's Video Sequence Editor (`strips.new_movie`) decoded all `393` frames (`720x1280` @ `30 FPS`, `13.10s`) natively at `~80 FPS` into lossless PNGs while preserving the `44.1 kHz` stereo `AAC` audio stream.
- **Exact Camera & Kinematic Structure of the Original 393-Frame Video**:
  - **Frames `1..182` (Isometric 3/4 View)**: Camera is `100%` static (`subpixel rail edge std = 0.031 px`). Crank completes 1 full `360°` revolution at constant angular speed (`~2.00°/frame`).
  - **Frames `183..212` (30-Frame Camera Orbit)**: Crank **pauses** aligned with the rail (`0°`) while the perspective camera orbits smoothly to a near-vertical top-down view (`~4.5°` off-vertical perspective tilt, visible on the left boss wall and bottom rail face).
  - **Frames `213..393` (Top-Down View)**: Camera is `100%` static (`subpixel rail edge std = 0.022 px`). Crank completes 1 full `360°` revolution (`180` frames at `2.00°/frame`; `MAD(f213, f393) = 0.37/255`).
- **Why Per-Frame 2D Recoloring (V1) Produced Flicker, Banding & Artifacts (Critical Lesson for V2)**:
  1. **Edge Flicker & Green Halos**: Per-frame binary morphological masks (`connectedComponentsWithStats`, `erode`/`dilate`, `max_c <= 89`) chatter by `±1 px` across frames on `AV1 yuv420p` mosquito noise and cast-shadow gradients. Static camera segments **must** use a single time-invariant `float32` silhouette matte.
  2. **4:2:0 Chroma Staircases on Diagonal Edges**: Rotating coral-to-blue directly on `yuv420p` 2x2-subsampled chroma creates jagged dark staircases along the moving diagonal connecting rod unless chroma differences `(Cr, Cb)` are smoothed (`sigma = 0.85–1.0`) independently of full-res `1x1` luma `Y` and deblocked at silhouette boundaries.
  3. **Surface Color Banding**: Multiplying 8-bit dark rail luma (`30..80`) by `2.18x` without 16/32-bit debanding + Triangular PDF (`TPDF`) dithering (`scene.render.dither_intensity = 1.5`) stretches 1-level `AV1` macroblock steps into visible green contour bands.
  4. **Un-Erased Orbit Text & Wavy Harmonic Blobs**: A fixed-ROI `spsolve` Laplace inpainter (`x=275..595, y=650..1015`) creates wavy pillowing gradients on flat channels and misses `'B. Cruz'` when the rail swings past `x=650, y=1050` during orbit frames `195..208`. Time-invariant albedo unmixing (`min(R,G,B)` white-ink separation + 1D rail-axis shading profile) eliminates both issues across all `393` frames.
  5. **Hardware Must Stay Black & Matte-vs-Glossy Contrast Multiplied**: The 3 joint assemblies (matte black oxide `6-lobe` socket-head cap screws at Back & Front, smooth chamfered black cap + spacer + bottom nut at Middle, and **mirror-glossy black cylindrical spacer** at Front reflecting the mint slider and rod collar) must be protected by smooth kinematic 3D-cylinder masks (`black_to_green_w = 0`), with specular bevel rims and mirror-spacer reflections multiplied rather than flattened.

---

## 11.11.2026 — Cross-Project Integration Rules (WhatsApp & GCP Cloud Offload)

- **WhatsApp Self-Notification Safety (`FIREFOX_CONTROL` + `ELEVATE_MEDIA_MONITOR`)**:
  - Always operate inside Firefox via WebDriver BiDi (`/Users/markobosko/Developer/FIREFOX_CONTROL/firefoxctl`, `127.0.0.1:9222`) — never hijack macOS screen mouse/keyboard focus.
  - **Strict Self-Chat Rule**: Automated messages/attachments may **ONLY** target Marko's own `(You)` self-chat (`+385 97 679 0768`, modeled on `/Users/markobosko/Developer/ELEVATE_MEDIA_MONITOR/tools/whatsapp_self.py`). Never send to any other contact or group.
- **Google Cloud `$300` Free Credit Alignment (`0193A0-F5144A-C98D4D`)**:
  - Billing Account `0193A0-F5144A-C98D4D` (`Organization 87869539786`, `auroville.email`, `$299.97` remaining credit expiring `2026-12-03`) is already governed by the `$285.00` hard safety cap (`$14.97` buffer, `min-instances = 0`) established in sister workspace `/Users/markobosko/Developer/ANTIGRAVITY_OFFLOAD_TO_CLOUD`. Any new Cloud Run / Vertex AI video-prompt service (`blender-video-ai-studio` or deployed onto `antigravity-cloud-offload`) must share the same `$285.00` cap and `min-instances = 0` scale-to-zero rule so idle cost is `$0.00`.

---
name: video-frame-precise-edit
description: >-
  Frame-by-frame surgical video editing, text/logo removal, material-selective
  recoloring, hardware preservation, and zero-flicker Blender 5.2 VSE / 3D
  compositing on macOS. Use this skill whenever editing rendered 3D mechanism
  videos, CAD animations, or studio product videos where frame-to-frame
  blending, zero edge flicker, zero color banding, and exact geometry/shadow
  preservation are required.
---

# Frame-Precise Video Editing & Blender 5.2 Compositing Skill

This skill codifies the mathematical and engineering methodology developed in `projects/04_how_rotation_becomes/` for performing **100% frame-aligned, zero-flicker, zero-banding** edits on rendered 3D studio videos (such as AV1/H.264 CAD animations) using **Blender 5.2 LTS** + **NumPy / SciPy / OpenCV**.

---

## 1. Decoding Modern Codecs (`AV1`) Reliably via Blender 5.2 VSE

System `ffmpeg` builds on macOS often lack `libdav1d` / hardware AV1 decoding and silently output `0` frames on YouTube/Shorts `AV1` MP4s. **Blender 5.2's internal FFmpeg/VSE decodes AV1 natively at ~80 FPS** into lossless PNG frames + extracted audio:

```python
# Decode any AV1/HEVC/H264 MP4 to lossless PNG sequence via Blender 5.2 VSE
import bpy

scene = bpy.context.scene
scene.sequence_editor_create()
seq = scene.sequence_editor
strip = seq.strips.new_movie(name="Source", filepath="/abs/path/input.mp4", channel=1, frame_start=1)

scene.frame_start = 1
scene.frame_end = strip.frame_final_duration
scene.render.resolution_x = strip.elements[0].orig_width
scene.render.resolution_y = strip.elements[0].orig_height
scene.render.image_settings.media_type = 'IMAGE'
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_depth = '16'  # Prefer 16-bit PNG to prevent 8-bit quantization steps!
scene.render.filepath = "/abs/path/frames/frame_"
bpy.ops.render.render(animation=True)
```

---

## 2. The Five Golden Rules for Zero Flicker, Zero Banding & 100% Blending

### Rule 1: Never Use Per-Frame Binary Morphological Thresholds on Static Camera Segments
- Per-frame `connectedComponentsWithStats`, `erode`, `dilate`, or hard pixel thresholds (`max_c >= 92`, `grad_v <= 3.6`) flip individual edge pixels ON/OFF between frame $t$ and $t+1$ due to `yuv420p` mosquito noise, causing **visible edge flickering and green/grey boundary halos**.
- **Fix**:
  1. Measure subpixel edge stability across frames (`std < 0.05 px` confirms static camera segments, e.g., `f=1..182` isometric and `f=213..393` top-down).
  2. Compute **one single static `float32` `[0..1]` anti-aliased silhouette matte** per static camera segment, and warp it via smooth planar homography $H(t)$ during camera orbit transitions (`f=183..212`).

### Rule 2: Time-Invariant Albedo Unmixing for Surface Text Removal (Instead of Per-Frame Harmonic Inpainting)
- Per-frame 2D Laplace harmonic inpainting (`spsolve`) samples discrete neighbor rings that fluctuate with compression noise, creating **wavy pillowing blobs** along flat CAD channels, and fails if the ROI box isn't tracked during camera orbits.
- **Fix**:
  - Surface text (`RGB ≈ 240` white ink on `RGB ≈ 55` dark rail) obeys linear illumination scaling:
    $$I(x, y, t) = L_{\text{light}}(x, y, t) \cdot \big((1 - \alpha_{\text{text}}(x, y)) \rho_{\text{rail}} + \alpha_{\text{text}}(x, y) \rho_{\text{white}}\big)$$
  - Extract $\alpha_{\text{text}}(x, y) \in [0, 1]$ **once** from an unoccluded, unshadowed reference frame per static view (warped by $H(t)$ during camera orbits), mask out pixels currently occluded by moving colored links (`chroma > 25`), and unmix along the 1D rail-axis shading profile. Even moving cast shadows from the connecting rod are preserved seamlessly with `0.000` temporal variance!

### Rule 3: Parametric 3D-Kinematic Hardware Masks to Preserve Black Bolts, Spacers & Nuts
- Global dark-pixel recoloring (`black -> green`) erroneously turns dark socket-head cap screws, cylindrical spacers, and bottom nuts green.
- **Fix**:
  1. Fit smooth $C^\infty$ harmonic Fourier trajectories $\theta(f) = \omega f + \phi_0$ (e.g. `2.000 deg/frame`, `180`-frame revolution, paused during camera orbit `f=182..213`) to the 3 joint centers:
     - **Back Pivot Socket-Head Cap Screw** (`6-lobe` hex/Torx recess, matte black oxide)
     - **Middle Flat Chamfered Cap + Cylindrical Spacer + Bottom Nut**
     - **Front Socket-Head Cap Screw + Mirror-Glossy Cylindrical Spacer**
  2. Evaluate smooth analytical 2D projected cylinder/ellipse masks `(cx(t), cy(t), rx(t), ry(t), dh(t))` with `1.2 px` subpixel feathering so `black_to_green_weight = 0.0` inside all hardware assemblies.

### Rule 4: Multiply Matte-vs-Reflective Surface Contrast & Update Secondary Color Reflections
- Study the PBR roughness hierarchy of the original render before recoloring:
  - **Ultra-matte studio floor** (`roughness ~ 0.85`): preserve `100%` untouched (`RGB(146, 146, 146)` + soft cast shadows).
  - **Satin CAD links & anodized rail** (`roughness ~ 0.35–0.45`): separate diffuse base luminance (`L <= 78`) from bevel specular highlights (`L > 78`) and boost specular rim contrast (`1.25x–1.40x`) so chamfered edges catch crisp studio softbox highlights.
  - **Semi-glossy Mint-Teal T-Slider** (`roughness ~ 0.15`): reflects the dark cylindrical spacer above it.
  - **Mirror-glossy Front Cylindrical Spacer** (`roughness ~ 0.03`): reflects the mint slider below, vertical studio softbox strip on its side, and the **rod collar immediately above it** (when recoloring the coral collar to blue, also rotate coral chroma reflections inside the glossy spacer to blue!).

### Rule 5: 32-Bit Linear Processing + Triangular PDF Dithering Against Color Banding
- Stretching 8-bit `yuv420p` dark rail values (`30..80`) by `>2x` in integer space turns `1`-LSB steps into visible `2–3`-level **color bands**.
- **Fix**:
  1. Process all frames in `float32` `[0.0, 255.0]` with directional `yuv420p` chroma deblocking (`sigma = 0.85` on `Cr, Cb` while keeping `1x1` sharp luma `Y`, plus gentle low-amplitude bilateral/guided debanding on smooth dark surfaces).
  2. Add `±0.5 LSB` Triangular PDF (`TPDF`) blue/uniform dither before quantization, or export `16-bit` PNGs into Blender 5.2 with `scene.render.dither_intensity = 1.5` and `constant_rate_factor = 'PERC_LOSSLESS'`.
  3. **Beware Blender's `#` Filename Placeholder**: Never pass `#` directly in `scene.render.filepath` (Blender expands `#` to frame numbers!). Render to a clean path first, then `os.replace()` to the final `#hashtag` filename.

---

## 3. Mandatory Frame-by-Frame Verification Protocol

Before marking any video render complete:
1. **Side-by-Side Zoom Inspection (`400%`)**: Generate `3x–4x` nearest-neighbor zoom pairs (`Original | Rendered`) on:
   - Back joint & boss bevels
   - Middle cap, spacer, and bottom nut
   - Front socket bolt, mirror-glossy spacer, and erased text zone
   - Mid-orbit transition frames (`f=188, 195, 202, 208`)
   - Top-down view (`f=260, 305, 365`)
2. **All-393-Frame Quantitative Audit**:
   - Studio floor untouched outside mechanism (`MAD < 0.5 / 255`).
   - Static rail temporal derivative `|I(t+1) - I(t)|` matches original noise floor (`0` flickering edge pixels).
   - Zero residual white text (`min(R,G,B) > 155` count in rail text polygon `== 0` across all 393 frames).
   - Black hardware neutral chroma (`chroma < 18`) verified on all 3 joints across all 393 frames.

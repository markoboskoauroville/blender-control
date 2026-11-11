# Blender 5.2.1 LTS (`bpy` / Python 3.13) Reference Guide

Verified against `/Applications/Blender.app/Contents/MacOS/Blender` (**Blender 5.2.1 LTS**, Python `3.13.13`, Apple M1 Pro 16-core Metal GPU).

---

## 1. Render Engines & Apple Silicon Metal GPU

Valid values for `bpy.context.scene.render.engine`:
- `'CYCLES'` — Ray-traced physically based path tracer (supports Apple M1 Pro 16-core Metal GPU).
- `'BLENDER_EEVEE'` — Real-time PBR raster/ray-hybrid renderer (note: `'BLENDER_EEVEE_NEXT'` was renamed back to `'BLENDER_EEVEE'` in Blender 4.2+/5.x).
- `'BLENDER_WORKBENCH'` — Fast technical/clay viewport renderer.

### Enabling Metal GPU for Cycles
```python
import bpy

scene = bpy.context.scene
scene.render.engine = 'CYCLES'

prefs = bpy.context.preferences.addons['cycles'].preferences
prefs.compute_device_type = 'METAL'
prefs.get_devices()
for dev in prefs.devices:
    dev.use = (dev.type == 'METAL')  # Enables 'Apple M1 Pro (GPU - 16 cores)'

scene.cycles.device = 'GPU'
scene.cycles.samples = 64
scene.cycles.use_denoising = True
```

---

## 2. Materials & Principled BSDF (Blender 5.2)

In Blender 5.x, `bpy.data.materials.new(name)` **automatically creates** `mat.node_tree` with a `Principled BSDF` and `Material Output` node (`mat.use_nodes` is always active by default).

### Exact `Principled BSDF` Input Socket Names in 5.2
- Core: `'Base Color'`, `'Metallic'`, `'Roughness'`, `'IOR'`, `'Alpha'`, `'Normal'`
- Diffuse/Subsurface: `'Diffuse Roughness'`, `'Subsurface Weight'`, `'Subsurface Radius'`, `'Subsurface Scale'`, `'Subsurface IOR'`, `'Subsurface Anisotropy'`
- Specular/Glass: `'Specular IOR Level'`, `'Specular Tint'`, `'Transmission Weight'`, `'Thin Wall'`
- Coat/Sheen/Emission/Iridescence:
  - `'Coat Weight'`, `'Coat Roughness'`, `'Coat IOR'`, `'Coat Tint'`, `'Coat Normal'`
  - `'Sheen Weight'`, `'Sheen Roughness'`, `'Sheen Tint'`
  - `'Emission Color'`, `'Emission Strength'`
  - `'Thin Film Thickness'`, `'Thin Film IOR'`

> **Gotcha**: Old 3.x socket names like `'Transmission'`, `'Clearcoat'`, `'Emission'`, or `'Specular'` will raise `KeyError` in Blender 5.2! Always use `'Transmission Weight'`, `'Coat Weight'`, `'Emission Color'`, and `'Specular IOR Level'`.

```python
def make_glass_material(name="StudioGlass", color=(0.85, 0.94, 1.0, 1.0), ior=1.52):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = 0.02
    bsdf.inputs["IOR"].default_value = ior
    bsdf.inputs["Transmission Weight"].default_value = 1.0
    bsdf.inputs["Coat Weight"].default_value = 0.25
    return mat
```

---

## 3. Animation, Keyframes & Layered/Slotted Actions (Blender 5.0+)

Blender 5.0+ uses **Slotted / Layered Actions**. `action.fcurves` **no longer exists directly** on `bpy.types.Action`!

### Inserting Keyframes (Unchanged)
```python
obj.location = (0.0, 0.0, 1.0)
obj.keyframe_insert(data_path="location", frame=1)
```

### Reading or Modifying F-Curves & Interpolation (Blender 5.2 Way)
Use `bpy_extras.anim_utils.action_get_channelbag_for_slot`:
```python
from bpy_extras import anim_utils

act = obj.animation_data.action
slot = obj.animation_data.action_slot
channelbag = anim_utils.action_get_channelbag_for_slot(act, slot)

for fcurve in channelbag.fcurves:
    for kp in fcurve.keyframe_points:
        kp.interpolation = 'LINEAR'  # or 'BEZIER', 'CONSTANT'
```

### Frame-Change Handlers (Procedural / Kinematic Animations)
For exact mathematical mechanisms (gears, linkages, waves), you can either bake keyframes per frame or attach a frame handler:
```python
def update_mechanism(scene):
    t = (scene.frame_current - scene.frame_start) / max(1, (scene.frame_end - scene.frame_start))
    # compute exact positions...
```
*(Tip: Baking keyframes for every frame `for f in range(start, end + 1)` ensures `.blend` files play back at 60 FPS in any Blender viewport without needing script auto-execution!)*

---

## 4. Video & Still Image Output Settings (Blender 5.2)

In Blender 5.2, `scene.render.image_settings.media_type` controls whether output is a single image, multilayer EXR, or video container (`'IMAGE'`, `'MULTI_LAYER_IMAGE'`, `'VIDEO'`).

### Still PNG Render
```python
scene.render.image_settings.media_type = 'IMAGE'
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGBA'
scene.render.filepath = "/abs/path/to/render.png"
bpy.ops.render.render(write_still=True)
```

### MP4 (H.264) Animation Render
```python
scene.render.image_settings.media_type = 'VIDEO'  # Automatically sets file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'
scene.render.ffmpeg.constant_rate_factor = 'HIGH'
scene.render.ffmpeg.ffmpeg_preset = 'GOOD'
scene.render.use_file_extension = False
scene.render.filepath = "/abs/path/to/animation.mp4"
bpy.ops.render.render(animation=True)
```

> **Gotcha (`#` in Filenames)**: Blender interprets `#` in `scene.render.filepath` as a frame-number placeholder (e.g. turning `#mechanism.mp4` into `1-393mechanism.mp4`). Always render to a `#`-free path first and `os.replace()` into target filenames containing `#` (`blender_control_bridge.py` handles this automatically).

---

## 5. Compositor in Blender 5.2

`scene.node_tree` was replaced by `scene.compositing_node_group` in Blender 5.0+.
To create or edit compositor nodes in 5.2, assign a `CompositorNodeTree` (`bpy.data.node_groups.new("Comp", "CompositorNodeTree")`) to `scene.compositing_node_group` and set `scene.use_nodes = True`.

---

## 6. Context Overrides in Live GUI Mode

When running scripts via the TCP timer bridge (`bpy.app.timers`), `bpy.context.area` and `bpy.context.region` are `None` unless overridden.
- Prefer **data API** (`bpy.data.meshes`, `bmesh`, `obj.modifiers.new(...)`, `scene.collection.objects.link(obj)`) over `bpy.ops` whenever possible — it is 10x faster and context-independent.
- When an operator requires a 3D Viewport context, wrap it with `bpy.context.temp_override`:
```python
wm = bpy.context.window_manager
for window in wm.windows:
    for area in window.screen.areas:
        if area.type == 'VIEW_3D':
            region = next(r for r in area.regions if r.type == 'WINDOW')
            with bpy.context.temp_override(window=window, area=area, region=region):
                bpy.ops.view3d.camera_to_view_selected()
            break
```

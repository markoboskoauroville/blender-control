"""
Test Project 02: Parametric Hexagonal Harmonic Wave Matrix
Demonstrates: Procedural bmesh hexagonal geometry, mathematical harmonic wave elevation,
shader variation across 169 instanced hex columns, dramatic rim/cyber lighting, and EEVEE PBR.
"""

import math
import bmesh
import bpy
import mathutils


def clear_scene():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for col in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras):
        for block in list(col):
            if block.users == 0:
                col.remove(block)


def create_hex_prism_mesh(name="HexPrismMesh", radius=0.46):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm,
        cap_ends=True,
        cap_tris=False,
        segments=6,
        radius1=radius,
        radius2=radius * 0.96,
        depth=1.0,
    )
    # Shift so base sits at z=0 and top is at z=1
    bmesh.ops.translate(bm, verts=bm.verts, vec=(0.0, 0.0, 0.5))
    bmesh.ops.bevel(
        bm,
        geom=list(bm.edges),
        offset=0.028,
        segments=2,
        profile=0.5,
        affect="EDGES",
    )
    bm.to_mesh(mesh)
    bm.free()
    for poly in mesh.polygons:
        poly.use_smooth = True
    return mesh


def make_hex_material(name, base_col, emit_col, emit_strength):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*base_col, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.88
    bsdf.inputs["Roughness"].default_value = 0.18
    bsdf.inputs["Coat Weight"].default_value = 0.3
    bsdf.inputs["Emission Color"].default_value = (*emit_col, 1.0)
    bsdf.inputs["Emission Strength"].default_value = emit_strength
    return mat


def build():
    clear_scene()
    scene = bpy.context.scene

    base_mesh = create_hex_prism_mesh(radius=0.47)

    # Create 8 gradient material tiers from dark titanium to saturated cyan & amber gold
    palette = []
    for i in range(8):
        t = i / 7.0
        if t < 0.65:
            u = t / 0.65
            base = (0.03 + 0.04 * u, 0.08 + 0.36 * u, 0.14 + 0.56 * u)
            emit = (0.0, 0.35 * u, 0.75 * u)
            strength = 0.05 + 0.45 * (u ** 2)
        else:
            u = (t - 0.65) / 0.35
            base = (0.07 + 0.85 * u, 0.44 + 0.24 * u, 0.70 - 0.52 * u)
            emit = (0.95 * u, 0.48 * u, 0.08)
            strength = 0.45 + 0.95 * u
        palette.append(make_hex_material(f"HexTier_{i}", base, emit, strength))

    # Build axial hexagonal grid (radius N = 7 -> 169 hex columns)
    grid_radius = 7
    hex_spacing = 0.54
    for q in range(-grid_radius, grid_radius + 1):
        r1 = max(-grid_radius, -q - grid_radius)
        r2 = min(grid_radius, -q + grid_radius)
        for r in range(r1, r2 + 1):
            x = hex_spacing * math.sqrt(3.0) * (q + r / 2.0)
            y = hex_spacing * 1.5 * r
            dist = math.hypot(x, y)
            angle = math.atan2(y, x)

            # Interference ripple + spiral harmonic
            wave = 0.5 + 0.5 * math.cos(dist * 1.35 - 2.0 * angle)
            envelope = math.exp(-0.045 * dist * dist)
            height = 0.35 + 2.35 * wave * envelope + 0.22 * math.sin(dist * 2.1)

            col_obj = bpy.data.objects.new(f"Hex_{q}_{r}", base_mesh.copy())
            scene.collection.objects.link(col_obj)
            col_obj.location = (x, y, 0.0)
            col_obj.scale = (1.0, 1.0, max(0.2, height))

            tier_idx = min(7, max(0, int((height - 0.25) / 2.55 * 7.99)))
            col_obj.data.materials.append(palette[tier_idx])

    # Reflective dark mirror base plane
    bpy.ops.mesh.primitive_plane_add(size=60.0, location=(0, 0, 0.02))
    floor = bpy.context.active_object
    floor.name = "MirrorDeck"
    mat_floor = bpy.data.materials.new("MirrorObsidian")
    bsdf_f = mat_floor.node_tree.nodes["Principled BSDF"]
    bsdf_f.inputs["Base Color"].default_value = (0.015, 0.02, 0.03, 1.0)
    bsdf_f.inputs["Metallic"].default_value = 0.92
    bsdf_f.inputs["Roughness"].default_value = 0.09
    floor.data.materials.append(mat_floor)

    # Dramatic studio lighting
    def add_light(name, loc, target, energy, color, size):
        ldata = bpy.data.lights.new(name=name, type="AREA")
        ldata.energy = energy
        ldata.color = color
        ldata.size = size
        lobj = bpy.data.objects.new(name, ldata)
        scene.collection.objects.link(lobj)
        lobj.location = loc
        lobj.rotation_euler = (mathutils.Vector(target) - mathutils.Vector(loc)).to_track_quat("-Z", "Y").to_euler()

    add_light("CyanBackLight", (-7.5, 8.5, 6.5), (0, 0, 0.8), 950.0, (0.25, 0.78, 1.0), 5.0)
    add_light("WarmSideKey", (8.5, -6.5, 7.2), (0, 0, 1.0), 780.0, (1.0, 0.78, 0.55), 4.5)
    add_light("OverheadFill", (0.0, 0.0, 11.0), (0, 0, 0.0), 320.0, (0.75, 0.85, 1.0), 7.0)

    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    scene.world = world
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.008, 0.012, 0.022, 1.0)
        bg.inputs["Strength"].default_value = 0.7

    # Isometric-style 46mm elevated camera framing full hexagonal wave field
    cam_data = bpy.data.cameras.new("MatrixCamera")
    cam_data.lens = 46.0
    cam_data.dof.use_dof = True
    cam_data.dof.focus_distance = 13.8
    cam_data.dof.aperture_fstop = 5.6
    cam_obj = bpy.data.objects.new("MatrixCamera", cam_data)
    scene.collection.objects.link(cam_obj)
    cam_obj.location = (9.6, -9.8, 7.2)
    cam_obj.rotation_euler = (mathutils.Vector((0.0, 0.0, 0.95)) - cam_obj.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam_obj

    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 64
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 1000
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"

    print("Built Project 02: Parametric Hexagonal Wave Matrix (169 columns)")


build()

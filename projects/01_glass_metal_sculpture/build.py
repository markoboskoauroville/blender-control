"""
Test Project 01: Architectural Glass & Brushed Gold Torus-Knot Studio Sculpture
Demonstrates: Parametric 3D curves, Cycles Metal GPU ray-traced glass refraction,
anisotropic brushed gold, cyclorama studio lighting, Depth of Field, and AgX color management.
"""

import math
import bpy
import mathutils


def clear_scene():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for col in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras, bpy.data.curves):
        for block in list(col):
            if block.users == 0:
                col.remove(block)


def make_material_gold():
    mat = bpy.data.materials.new("BrushedChampagneGold")
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.96, 0.76, 0.42, 1.0)
    bsdf.inputs["Metallic"].default_value = 1.0
    bsdf.inputs["Roughness"].default_value = 0.16
    bsdf.inputs["Anisotropic"].default_value = 0.55
    bsdf.inputs["Coat Weight"].default_value = 0.2
    return mat


def make_material_glass():
    mat = bpy.data.materials.new("ArchitecturalCrystalGlass")
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.88, 0.96, 1.0, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.0
    bsdf.inputs["Roughness"].default_value = 0.015
    bsdf.inputs["IOR"].default_value = 1.54
    bsdf.inputs["Transmission Weight"].default_value = 1.0
    bsdf.inputs["Thin Film Thickness"].default_value = 380.0
    bsdf.inputs["Thin Film IOR"].default_value = 1.38
    return mat


def make_material_pedestal():
    mat = bpy.data.materials.new("ObsidianSlate")
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.035, 0.038, 0.048, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.25
    bsdf.inputs["Roughness"].default_value = 0.22
    bsdf.inputs["Coat Weight"].default_value = 0.35
    bsdf.inputs["Coat Roughness"].default_value = 0.08
    return mat


def make_material_core_glow():
    mat = bpy.data.materials.new("WarmCoreEmitter")
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (1.0, 0.65, 0.3, 1.0)
    bsdf.inputs["Emission Color"].default_value = (1.0, 0.58, 0.22, 1.0)
    bsdf.inputs["Emission Strength"].default_value = 14.0
    return mat


def create_torus_knot(name, p=3, q=5, major_r=1.35, minor_r=0.52, bevel=0.14, steps=320):
    curve_data = bpy.data.curves.new(name=name, type="CURVE")
    curve_data.dimensions = "3D"
    curve_data.bevel_depth = bevel
    curve_data.bevel_resolution = 12
    curve_data.use_fill_caps = True

    spline = curve_data.splines.new("NURBS")
    spline.points.add(steps - 1)
    for i in range(steps):
        t = (2.0 * math.pi * i) / steps
        r = major_r + minor_r * math.cos(q * t)
        x = r * math.cos(p * t)
        y = r * math.sin(p * t)
        z = minor_r * math.sin(q * t)
        spline.points[i].co = (x, y, z, 1.0)

    spline.use_cyclic_u = True
    spline.order_u = 4
    spline.resolution_u = 16

    obj = bpy.data.objects.new(name, curve_data)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def build():
    clear_scene()
    scene = bpy.context.scene

    mat_gold = make_material_gold()
    mat_glass = make_material_glass()
    mat_slate = make_material_pedestal()
    mat_glow = make_material_core_glow()

    # Studio floor & infinity backdrop
    bpy.ops.mesh.primitive_plane_add(size=40.0, location=(0, 0, 0))
    floor = bpy.context.active_object
    floor.name = "StudioFloor"
    floor.data.materials.append(mat_slate)

    # Tiered cylindrical pedestal
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=1.85, depth=0.22, location=(0, 0, 0.11))
    ped1 = bpy.context.active_object
    ped1.name = "PedestalBase"
    bpy.ops.object.shade_smooth()
    bevel1 = ped1.modifiers.new("Bevel", "BEVEL")
    bevel1.width = 0.02
    bevel1.segments = 4
    ped1.data.materials.append(mat_slate)

    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=1.35, depth=0.06, location=(0, 0, 0.25))
    ped_ring = bpy.context.active_object
    ped_ring.name = "GoldAccentRing"
    bpy.ops.object.shade_smooth()
    bevel2 = ped_ring.modifiers.new("Bevel", "BEVEL")
    bevel2.width = 0.012
    bevel2.segments = 3
    ped_ring.data.materials.append(mat_gold)

    # Brushed Gold (3,5) Torus Knot
    knot = create_torus_knot("GoldTorusKnot", p=2, q=3, major_r=1.05, minor_r=0.42, bevel=0.115, steps=280)
    knot.location = (0, 0, 1.85)
    knot.rotation_euler = (math.radians(22), math.radians(-12), math.radians(18))
    knot.data.materials.append(mat_gold)

    # Interlocking Architectural Crystal Glass Mobius/Torus Ring
    bpy.ops.mesh.primitive_torus_add(
        major_segments=128,
        minor_segments=48,
        major_radius=1.32,
        minor_radius=0.18,
        location=(0, 0, 1.85),
    )
    glass_torus = bpy.context.active_object
    glass_torus.name = "CrystalGlassRing"
    glass_torus.rotation_euler = (math.radians(68), math.radians(18), math.radians(-24))
    bpy.ops.object.shade_smooth()
    glass_torus.data.materials.append(mat_glass)

    # Floating luminous core sphere inside glass + gold cage
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=0.28, location=(0, 0, 1.85))
    core = bpy.context.active_object
    core.name = "LuminousCore"
    bpy.ops.object.shade_smooth()
    core.data.materials.append(mat_glow)

    # Orbiting glass droplets
    for i in range(6):
        ang = i * (2 * math.pi / 6) + 0.3
        pos = (2.05 * math.cos(ang), 2.05 * math.sin(ang), 1.05 + 0.35 * math.sin(2 * ang))
        bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=0.14, location=pos)
        orb = bpy.context.active_object
        orb.name = f"GlassOrb_{i+1}"
        bpy.ops.object.shade_smooth()
        orb.data.materials.append(mat_glass if i % 2 == 0 else mat_gold)

    # Three-point studio area lighting
    def add_area_light(name, loc, target, energy, color, size):
        ldata = bpy.data.lights.new(name=name, type="AREA")
        ldata.energy = energy
        ldata.color = color
        ldata.size = size
        lobj = bpy.data.objects.new(name, ldata)
        scene.collection.objects.link(lobj)
        lobj.location = loc
        direction = mathutils.Vector(target) - mathutils.Vector(loc)
        lobj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
        return lobj

    target_pt = (0.0, 0.0, 1.75)
    add_area_light("KeyLight_Warm", (4.5, -4.2, 5.2), target_pt, 520.0, (1.0, 0.94, 0.86), 3.2)
    add_area_light("RimLight_Cool", (-4.8, 3.8, 4.4), target_pt, 680.0, (0.62, 0.82, 1.0), 2.6)
    add_area_light("TopFill_Soft", (0.0, -0.5, 6.8), target_pt, 260.0, (0.95, 0.97, 1.0), 4.5)

    # World dark studio gradient
    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    scene.world = world
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.014, 0.018, 0.026, 1.0)
        bg.inputs["Strength"].default_value = 0.8

    # Portrait 50mm camera with subtle Depth of Field framing full sculpture + pedestal
    cam_data = bpy.data.cameras.new("StudioCamera")
    cam_data.lens = 50.0
    cam_data.dof.use_dof = True
    cam_data.dof.focus_distance = 7.95
    cam_data.dof.aperture_fstop = 4.5
    cam_obj = bpy.data.objects.new("StudioCamera", cam_data)
    scene.collection.objects.link(cam_obj)
    cam_obj.location = (5.75, -5.45, 2.85)
    cam_dir = mathutils.Vector((0.0, 0.0, 1.55)) - cam_obj.location
    cam_obj.rotation_euler = cam_dir.to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam_obj

    # Render & Color Management Settings
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 64
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 1000
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"

    print("Built Project 01: Studio Glass & Gold Sculpture")


build()

"""
Test Project 03: Tusi Couple / Cardano Hypocycloid Straight-Line Mechanism
("How Rotation Becomes a Straight Line")
Demonstrates: Exact mathematical kinematics (rotary crank + rolling planetary gear
converting circular motion into 3 intersecting non-colliding straight-line shuttle motions),
Blender 5.2 Slotted Action linear keyframe animation (120 frames @ 30 FPS),
emerald-green machined housing + cobalt-blue rotor/sliders + brushed steel pins.
"""

import math
import bmesh
import bpy
import mathutils
from bpy_extras import anim_utils


def clear_scene():
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for col in (
        bpy.data.meshes,
        bpy.data.materials,
        bpy.data.lights,
        bpy.data.cameras,
        bpy.data.curves,
        bpy.data.actions,
    ):
        for block in list(col):
            if block.users == 0:
                col.remove(block)


def make_pbr_mat(name, color, metallic=0.8, roughness=0.22, coat=0.25, emit_strength=0.0):
    mat = bpy.data.materials.new(name)
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Coat Weight"].default_value = coat
    if emit_strength > 0.0:
        bsdf.inputs["Emission Color"].default_value = (*color, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emit_strength
    return mat


def create_ring_mesh(name, inner_r, outer_r, height, segments=128):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    verts_bot_in = []
    verts_bot_out = []
    verts_top_in = []
    verts_top_out = []
    for i in range(segments):
        ang = 2.0 * math.pi * i / segments
        ca, sa = math.cos(ang), math.sin(ang)
        verts_bot_in.append(bm.verts.new((inner_r * ca, inner_r * sa, 0.0)))
        verts_bot_out.append(bm.verts.new((outer_r * ca, outer_r * sa, 0.0)))
        verts_top_in.append(bm.verts.new((inner_r * ca, inner_r * sa, height)))
        verts_top_out.append(bm.verts.new((outer_r * ca, outer_r * sa, height)))

    for i in range(segments):
        j = (i + 1) % segments
        # Top & bottom faces
        bm.faces.new((verts_top_in[i], verts_top_out[i], verts_top_out[j], verts_top_in[j]))
        bm.faces.new((verts_bot_in[j], verts_bot_out[j], verts_bot_out[i], verts_bot_in[i]))
        # Inner & outer walls
        bm.faces.new((verts_bot_in[i], verts_top_in[i], verts_top_in[j], verts_bot_in[j]))
        bm.faces.new((verts_bot_out[j], verts_top_out[j], verts_top_out[i], verts_bot_out[i]))

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    for p in mesh.polygons:
        p.use_smooth = True
    return mesh


def set_linear_fcurves(obj):
    if not obj.animation_data or not obj.animation_data.action:
        return
    act = obj.animation_data.action
    slot = obj.animation_data.action_slot
    cb = anim_utils.action_get_channelbag_for_slot(act, slot)
    if not cb:
        return
    for fc in cb.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"


def build():
    clear_scene()
    scene = bpy.context.scene

    R = 1.25  # Planetary rotor pitch radius; outer ring pitch radius = 2 * R = 2.50
    OUTER_PITCH = 2.0 * R
    FRAME_START = 1
    FRAME_END = 120
    scene.frame_start = FRAME_START
    scene.frame_end = FRAME_END
    scene.render.fps = 30

    # Materials (Emerald Green Housing + Cobalt/Sapphire Blue Rotor & Sliders + Brushed Steel)
    mat_emerald_dark = make_pbr_mat("EmeraldBase", (0.04, 0.24, 0.14), metallic=0.65, roughness=0.26, coat=0.35)
    mat_emerald_rim = make_pbr_mat("EmeraldRim", (0.08, 0.44, 0.24), metallic=0.78, roughness=0.18, coat=0.4)
    mat_blue_rotor = make_pbr_mat("CobaltRotor", (0.08, 0.34, 0.88), metallic=0.75, roughness=0.18, coat=0.45)
    mat_blue_slider = make_pbr_mat("SapphireSlider", (0.14, 0.52, 0.98), metallic=0.65, roughness=0.16, coat=0.5)
    mat_cyan_line = make_pbr_mat("GuideLaserLine", (0.22, 0.78, 1.0), metallic=0.1, roughness=0.2, emit_strength=3.2)
    mat_steel = make_pbr_mat("BrushedSteel", (0.82, 0.85, 0.89), metallic=0.96, roughness=0.15, coat=0.2)
    mat_brass = make_pbr_mat("CenterCrankBrass", (0.92, 0.74, 0.34), metallic=0.95, roughness=0.18, coat=0.2)
    mat_studio = make_pbr_mat("StudioBackdrop", (0.025, 0.045, 0.038), metallic=0.2, roughness=0.35, coat=0.1)

    # Studio tabletop
    bpy.ops.mesh.primitive_plane_add(size=45.0, location=(0, 0, -0.25))
    table = bpy.context.active_object
    table.name = "WorkshopTable"
    table.data.materials.append(mat_studio)

    # Base Emerald Cylindrical Plate
    bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=OUTER_PITCH + 0.58, depth=0.24, location=(0, 0, -0.12))
    base_plate = bpy.context.active_object
    base_plate.name = "EmeraldHousingBase"
    bpy.ops.object.shade_smooth()
    bev = base_plate.modifiers.new("Bevel", "BEVEL")
    bev.width = 0.03
    bev.segments = 4
    base_plate.data.materials.append(mat_emerald_dark)

    # Outer Stationary Ring Wall (inner radius = 2R + clearance)
    ring_mesh = create_ring_mesh("OuterStatorRing", inner_r=OUTER_PITCH + 0.08, outer_r=OUTER_PITCH + 0.52, height=0.42, segments=128)
    outer_ring = bpy.data.objects.new("OuterStatorRing", ring_mesh)
    scene.collection.objects.link(outer_ring)
    outer_ring.location = (0, 0, 0.0)
    bev_r = outer_ring.modifiers.new("Bevel", "BEVEL")
    bev_r.width = 0.02
    bev_r.segments = 3
    outer_ring.data.materials.append(mat_emerald_rim)

    # 12 decorative perimeter socket bolts on the green outer ring
    for b_idx in range(12):
        ang = 2.0 * math.pi * b_idx / 12.0
        bx = (OUTER_PITCH + 0.30) * math.cos(ang)
        by = (OUTER_PITCH + 0.30) * math.sin(ang)
        bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.065, depth=0.08, location=(bx, by, 0.44))
        bolt = bpy.context.active_object
        bolt.name = f"PerimeterBolt_{b_idx+1}"
        bpy.ops.object.shade_smooth()
        bolt.data.materials.append(mat_steel)

    # 3 Straight-Line Guide Rails (at 0 deg, 60 deg, 120 deg) spanning full 4R diameter
    track_angles = [0.0, math.pi / 3.0, 2.0 * math.pi / 3.0]
    for idx, alpha in enumerate(track_angles):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.015))
        rail = bpy.context.active_object
        rail.name = f"LinearGuideTrack_{idx+1}"
        rail.scale = (2.0 * OUTER_PITCH + 0.08, 0.032, 0.014)
        rail.rotation_euler = (0, 0, alpha)
        rail.data.materials.append(mat_cyan_line)

    # Center Pivot Bearing + Rotating Brass Crank Arm (radius = R)
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.18, depth=0.18, location=(0, 0, 0.06))
    center_hub = bpy.context.active_object
    center_hub.name = "CenterBearing"
    bpy.ops.object.shade_smooth()
    center_hub.data.materials.append(mat_steel)

    crank_pivot = bpy.data.objects.new("CrankPivot", None)
    scene.collection.objects.link(crank_pivot)
    crank_pivot.location = (0, 0, 0.08)

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(R / 2.0, 0, 0.0))
    crank_arm = bpy.context.active_object
    crank_arm.name = "DriveCrankArm"
    crank_arm.scale = (R / 2.0 + 0.14, 0.11, 0.035)
    bev_c = crank_arm.modifiers.new("Bevel", "BEVEL")
    bev_c.width = 0.012
    bev_c.segments = 3
    crank_arm.data.materials.append(mat_brass)
    crank_arm.parent = crank_pivot

    # Inner Planetary Blue Rotor Disk (radius = R, with central bore for lightness)
    rotor_mesh = create_ring_mesh("PlanetaryRotorMesh", inner_r=0.26, outer_r=R + 0.04, height=0.14, segments=96)
    rotor = bpy.data.objects.new("PlanetaryBlueRotor", rotor_mesh)
    scene.collection.objects.link(rotor)
    bev_rot = rotor.modifiers.new("Bevel", "BEVEL")
    bev_rot.width = 0.015
    bev_rot.segments = 3
    rotor.data.materials.append(mat_blue_rotor)

    # Rotor center steel axle pin
    bpy.ops.mesh.primitive_cylinder_add(vertices=36, radius=0.14, depth=0.22, location=(0, 0, 0.07))
    rotor_axle = bpy.context.active_object
    rotor_axle.name = "RotorCenterAxle"
    bpy.ops.object.shade_smooth()
    rotor_axle.data.materials.append(mat_brass)
    rotor_axle.parent = rotor

    # 3 Circumference Drive Pins + 3 Linear Shuttle Blocks
    shuttles = []
    for idx, alpha in enumerate(track_angles):
        # Local angle on rotor = 2 * alpha, at radius R
        local_ang = 2.0 * alpha
        px = R * math.cos(local_ang)
        py = R * math.sin(local_ang)

        bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.075, depth=0.26, location=(px, py, 0.16))
        pin = bpy.context.active_object
        pin.name = f"RotorDrivePin_{idx+1}"
        bpy.ops.object.shade_smooth()
        pin.data.materials.append(mat_steel)
        pin.parent = rotor

        # Sapphire Blue Shuttle Block gliding purely along straight line angle `alpha`
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.30))
        shuttle = bpy.context.active_object
        shuttle.name = f"LinearShuttle_{idx+1}"
        shuttle.scale = (0.24, 0.15, 0.065)
        bev_s = shuttle.modifiers.new("Bevel", "BEVEL")
        bev_s.width = 0.02
        bev_s.segments = 3
        shuttle.data.materials.append(mat_blue_slider)

        # Steel bearing collar on top of shuttle
        bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.095, depth=0.04, location=(0, 0, 0.06))
        collar = bpy.context.active_object
        collar.name = f"ShuttleCollar_{idx+1}"
        bpy.ops.object.shade_smooth()
        collar.data.materials.append(mat_steel)
        collar.parent = shuttle

        shuttles.append((shuttle, alpha))

    # Bake exact 120-frame seamless loop (frames 1..120 covers 1 full crank revolution)
    num_frames = FRAME_END - FRAME_START + 1
    for f in range(FRAME_START, FRAME_END + 1):
        # Seamless loop: frame 1 = 0 rad, frame 121 would = 2*pi
        theta = 2.0 * math.pi * (f - FRAME_START) / num_frames

        # Crank rotates by +theta
        crank_pivot.rotation_euler = (0.0, 0.0, theta)
        crank_pivot.keyframe_insert(data_path="rotation_euler", frame=f)

        # Planetary rotor center orbits at radius R with angle +theta, and spins by -theta
        rotor.location = (R * math.cos(theta), R * math.sin(theta), 0.12)
        rotor.rotation_euler = (0.0, 0.0, -theta)
        rotor.keyframe_insert(data_path="location", frame=f)
        rotor.keyframe_insert(data_path="rotation_euler", frame=f)

        # Each shuttle translates strictly along its straight line axis `alpha`!
        for shuttle, alpha in shuttles:
            s_dist = 2.0 * R * math.cos(theta - alpha)
            shuttle.location = (s_dist * math.cos(alpha), s_dist * math.sin(alpha), 0.31)
            shuttle.rotation_euler = (0.0, 0.0, alpha)
            shuttle.keyframe_insert(data_path="location", frame=f)
            if f == FRAME_START:
                shuttle.keyframe_insert(data_path="rotation_euler", frame=f)

    # Set linear keyframe interpolation for constant angular velocity
    set_linear_fcurves(crank_pivot)
    set_linear_fcurves(rotor)
    for shuttle, _ in shuttles:
        set_linear_fcurves(shuttle)

    scene.frame_set(18)  # Dynamic hero angle for still renders

    # Crisp Engineering Studio Lighting
    def add_area(name, loc, target, energy, color, size):
        ld = bpy.data.lights.new(name=name, type="AREA")
        ld.energy = energy
        ld.color = color
        ld.size = size
        lo = bpy.data.objects.new(name, ld)
        scene.collection.objects.link(lo)
        lo.location = loc
        lo.rotation_euler = (mathutils.Vector(target) - mathutils.Vector(loc)).to_track_quat("-Z", "Y").to_euler()

    add_area("KeyLight_Main", (4.5, -5.0, 6.5), (0, 0, 0.2), 620.0, (1.0, 0.98, 0.94), 4.5)
    add_area("RimLight_EmeraldCyan", (-5.5, 4.8, 5.0), (0, 0, 0.2), 540.0, (0.65, 0.92, 1.0), 3.8)
    add_area("TopSoftBox", (0.0, 0.5, 7.5), (0, 0, 0.0), 340.0, (0.95, 0.98, 1.0), 5.5)

    world = bpy.data.worlds.get("World") or bpy.data.worlds.new("World")
    scene.world = world
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.012, 0.022, 0.018, 1.0)
        bg.inputs["Strength"].default_value = 0.85

    # High-angle three-quarter engineering showcase camera framing full mechanism
    cam_data = bpy.data.cameras.new("MechanismCamera")
    cam_data.lens = 36.0
    cam_obj = bpy.data.objects.new("MechanismCamera", cam_data)
    scene.collection.objects.link(cam_obj)
    cam_obj.location = (0.0, -5.85, 5.75)
    cam_obj.rotation_euler = (mathutils.Vector((0.0, 0.05, 0.12)) - cam_obj.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam_obj

    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 48
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"

    print("Built Project 03: Straight-Line Hypocycloid Mechanism (120 frames baked)")


build()

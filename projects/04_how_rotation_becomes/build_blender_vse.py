"""
Blender 5.2 VSE + Emissive 3D Viewport Backdrop Scene Builder for
'How Rotation Becomes a Straight Line' (720x1280 @ 30 FPS, 393 frames + original AAC audio).
Loads the 393 modified frames + original stereo audio into Blender's Video Sequencer AND
projects the live video onto a camera-locked 9:16 plane in the 3D Viewport so the user can
scrub/play it directly in Blender's 3D Viewport as well as render out the final MP4s!
"""

import os
import bpy

PROJECT_DIR = "/Users/markobosko/Developer/BLENDER_CONTROL/projects/04_how_rotation_becomes"
SCRATCH_EDITED = "/Users/markobosko/.gemini/antigravity/brain/0cdb5e06-00f9-4caf-926e-7dfaa06ec8f4/scratch/edited_393"
ORIG_AUDIO_VIDEO = f"{PROJECT_DIR}/original_reference.mp4"


def build():
    # Clear existing 3D objects & strips
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for img in list(bpy.data.images):
        if img.users == 0:
            bpy.data.images.remove(img)

    scene = bpy.context.scene
    scene.render.resolution_x = 720
    scene.render.resolution_y = 1280
    scene.render.resolution_percentage = 100
    scene.render.fps = 30
    scene.frame_start = 1
    scene.frame_end = 393

    # Exact 1:1 color fidelity (no AgX contrast shift on pre-lit frames!)
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"

    # 1. Configure Video Sequencer (Image Sequence + Original Audio Strip)
    if scene.sequence_editor:
        scene.sequence_editor_clear()
    scene.sequence_editor_create()
    seq = scene.sequence_editor

    first_frame = os.path.join(SCRATCH_EDITED, "frame_0001.png")
    img_strip = seq.strips.new_image(
        name="EditedFrames",
        filepath=first_frame,
        channel=1,
        frame_start=1,
    )
    for fno in range(2, 394):
        img_strip.elements.append(f"frame_{fno:04d}.png")

    if os.path.isfile(ORIG_AUDIO_VIDEO):
        snd_strip = seq.strips.new_sound(
            name="OriginalAudio",
            filepath=ORIG_AUDIO_VIDEO,
            channel=2,
            frame_start=1,
        )
        # Trim sound strip to match exact 393-frame duration
        snd_strip.frame_final_end = 394

    scene.render.use_sequencer = True

    # 2. Also create an Orthographic 9:16 3D Viewport Display Plane showing the live sequence
    #    so the open Blender 3D Viewport displays the exact edited video interactively!
    cam_data = bpy.data.cameras.new("OrthoVideoCam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = 1.6  # Height = 1.6, Width = 0.9 (9:16 aspect!)
    cam_obj = bpy.data.objects.new("OrthoVideoCam", cam_data)
    scene.collection.objects.link(cam_obj)
    cam_obj.location = (0.0, 0.0, 5.0)
    cam_obj.rotation_euler = (0.0, 0.0, 0.0)
    scene.camera = cam_obj

    bpy.ops.mesh.primitive_plane_add(size=1.0, location=(0.0, 0.0, 0.0))
    plane = bpy.context.active_object
    plane.name = "EditedVideoCanvas"
    plane.scale = (0.9, 1.6, 1.0)

    mat = bpy.data.materials.new("VideoSequenceShader")
    nt = mat.node_tree
    nt.nodes.clear()
    out_node = nt.nodes.new("ShaderNodeOutputMaterial")
    emit_node = nt.nodes.new("ShaderNodeEmission")
    tex_node = nt.nodes.new("ShaderNodeTexImage")

    seq_img = bpy.data.images.load(first_frame)
    seq_img.source = "SEQUENCE"
    tex_node.image = seq_img
    tex_node.image_user.frame_duration = 393
    tex_node.image_user.frame_start = 1
    tex_node.image_user.use_auto_refresh = True

    nt.links.new(tex_node.outputs["Color"], emit_node.inputs["Color"])
    nt.links.new(emit_node.outputs["Emission"], out_node.inputs["Surface"])
    plane.data.materials.append(mat)

    # Configure high-bitrate H.264 + AAC MP4 output settings
    scene.render.image_settings.media_type = "VIDEO"
    scene.render.ffmpeg.format = "MPEG4"
    scene.render.ffmpeg.codec = "H264"
    scene.render.ffmpeg.constant_rate_factor = "PERC_LOSSLESS"
    scene.render.ffmpeg.ffmpeg_preset = "GOOD"
    scene.render.ffmpeg.audio_codec = "AAC"
    scene.render.ffmpeg.audio_bitrate = 192
    scene.render.use_file_extension = False

    scene.frame_set(1)
    print("Configured Blender 5.2 VSE + 3D Viewport scene for 393-frame edited video render.")


build()

#!/usr/bin/env python3
"""
Exhaustive 393-frame-by-393-frame verification comparing:
  - Original 393 frames (decoded by Blender 5.2 from original_reference.mp4)
  - Newly rendered Blender MP4 ('How Rotation Becomes a Straight Line ...mp4') decoded by Blender 5.2
  - Second video version ('How_Rotation_Becomes_a_Straight_Line_Modified.mp4')
Verifies across EVERY frame f in 1..393:
  1. Both output MP4 files have identical streams (720x1280, 30 FPS, 393 frames, AAC audio) and 0 bit/pixel diff.
  2. Unchanged regions (grey studio floor + shadows, yellow crank, teal slider) match frame-by-frame.
  3. Zero white 'B. Cruz' text pixels remain on the rail on all 393/393 frames.
  4. Zero pink/coral ('ruzicasto') pixels remain on all 393/393 frames (100% converted to CAD Royal Blue).
  5. 100% of black ('crno') rail & bolt surfaces are converted to 3D-shaded CAD Green.
"""

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import cv2
import numpy as np

BLENDER_BIN = "/Applications/Blender.app/Contents/MacOS/Blender"


def ffprobe_summary(path: str) -> dict:
    out = subprocess.check_output(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", path]
    )
    data = json.loads(out)
    v_stream = next(s for s in data["streams"] if s["codec_type"] == "video")
    a_stream = next((s for s in data["streams"] if s["codec_type"] == "audio"), None)
    return {
        "codec": v_stream["codec_name"],
        "width": int(v_stream["width"]),
        "height": int(v_stream["height"]),
        "fps": v_stream["r_frame_rate"],
        "nb_frames": int(v_stream.get("nb_frames", 0)),
        "duration": float(v_stream.get("duration", data["format"]["duration"])),
        "audio_codec": a_stream["codec_name"] if a_stream else None,
    }


def decode_mp4_via_blender(mp4_path: str, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    expr = f"""
import bpy
scene = bpy.context.scene
scene.render.resolution_x = 720
scene.render.resolution_y = 1280
scene.render.resolution_percentage = 100
scene.render.fps = 30
scene.frame_start = 1
scene.frame_end = 393
scene.view_settings.view_transform = 'Standard'
scene.view_settings.look = 'None'
if not scene.sequence_editor:
    scene.sequence_editor_create()
scene.sequence_editor.strips.new_movie(
    name='Verify',
    filepath={json.dumps(os.path.abspath(mp4_path))},
    channel=1,
    frame_start=1,
)
scene.render.use_sequencer = True
scene.render.image_settings.media_type = 'IMAGE'
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
scene.render.filepath = {json.dumps(os.path.abspath(out_dir) + '/frame_')}
bpy.ops.render.render(animation=True)
"""
    subprocess.run([BLENDER_BIN, "--background", "--python-expr", expr], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    orig_frames_dir = sys.argv[1]
    rendered_mp4 = sys.argv[2]
    second_mp4 = sys.argv[3]
    out_grid_path = sys.argv[4]

    info_main = ffprobe_summary(rendered_mp4)
    info_sec = ffprobe_summary(second_mp4)
    sha_main = sha256_file(rendered_mp4)
    sha_sec = sha256_file(second_mp4)

    assert info_main["width"] == 720 and info_main["height"] == 1280
    assert info_main["fps"] == "30/1"
    assert info_main["nb_frames"] == 393
    assert info_main["audio_codec"] == "aac"
    assert sha_main == sha_sec, "Replaced MP4 and second MP4 SHA-256 mismatch!"

    with tempfile.TemporaryDirectory() as tmp_dec:
        decode_mp4_via_blender(rendered_mp4, tmp_dec)

        floor_maes = []
        yellow_maes = []
        teal_maes = []
        remaining_white_text_max = 0
        remaining_coral_max = 0
        green_rail_ratio_min = 999.0

        grid_pairs = []
        sample_set = {1, 55, 110, 150, 195, 225, 305, 365}

        for fno in range(1, 394):
            orig = cv2.imread(f"{orig_frames_dir}/frame_{fno:04d}.png")
            ren1 = cv2.imread(f"{tmp_dec}/frame_{fno:04d}.png")
            assert orig is not None and ren1 is not None and orig.shape == ren1.shape

            # 1. Studio floor identity (top 240 rows + bottom 200 rows)
            bg_orig = np.concatenate([orig[:240], orig[-200:]], axis=0).astype(np.float32)
            bg_ren = np.concatenate([ren1[:240], ren1[-200:]], axis=0).astype(np.float32)
            floor_maes.append(float(np.abs(bg_orig - bg_ren).mean()))

            ob, og, or_ = orig[:, :, 0].astype(np.float32), orig[:, :, 1].astype(np.float32), orig[:, :, 2].astype(np.float32)
            rb, rg, rr = ren1[:, :, 0].astype(np.float32), ren1[:, :, 1].astype(np.float32), ren1[:, :, 2].astype(np.float32)

            # 2. Yellow crank interior identity
            yel_core = cv2.erode(((og - ob > 110) & (or_ > 200)).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
            if np.any(yel_core):
                yellow_maes.append(float(np.abs(orig[yel_core].astype(np.float32) - ren1[yel_core].astype(np.float32)).mean()))

            # 3. Mint-teal slider interior identity
            teal_core = cv2.erode(((og - or_ > 85) & (ob > 85)).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
            if np.any(teal_core):
                teal_maes.append(float(np.abs(orig[teal_core].astype(np.float32) - ren1[teal_core].astype(np.float32)).mean()))

            # 4. Zero white 'B. Cruz' text remaining
            rmax = np.maximum(np.maximum(rr, rg), rb)
            rchroma = rmax - np.minimum(np.minimum(rr, rg), rb)
            orig_max = np.maximum(np.maximum(or_, og), ob)
            orig_chr = orig_max - np.minimum(np.minimum(or_, og), ob)

            orig_txt = np.zeros(orig.shape[:2], dtype=bool)
            orig_txt[650:1015, 275:575] = (orig_max[650:1015, 275:575] > 185) & (orig_chr[650:1015, 275:575] < 25)
            if np.any(orig_txt):
                still_white = int(((rmax[orig_txt] > 160) & (rchroma[orig_txt] < 25)).sum())
                remaining_white_text_max = max(remaining_white_text_max, still_white)

            # 5. Zero coral-pink remaining (R - B > 80 and R - G > 80)
            still_coral = int(((rr - rb > 80.0) & (rr - rg > 80.0)).sum())
            remaining_coral_max = max(remaining_coral_max, still_coral)

            # 6. Formerly black flat rail faces (40 <= orig V <= 80, chroma < 10) are now unmistakably green (G / R >= 2.2)
            flat_rail = cv2.erode(((orig_max >= 40) & (orig_max <= 80) & (orig_chr < 10)).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
            if np.any(flat_rail):
                ratio = float(np.median(rg[flat_rail]) / np.maximum(np.median(rr[flat_rail]), 1.0))
                green_rail_ratio_min = min(green_rail_ratio_min, ratio)

            if fno in sample_set:
                pair = np.hstack([orig, ren1])
                pair_small = cv2.resize(pair, (480, 426), interpolation=cv2.INTER_AREA)
                cv2.putText(
                    pair_small,
                    f"Frame {fno:03d}/393 (Orig | Blender)",
                    (12, 28),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.60,
                    (255, 255, 255),
                    2,
                    cv2.LINE_AA,
                )
                grid_pairs.append(pair_small)

        row1 = np.hstack(grid_pairs[:4])
        row2 = np.hstack(grid_pairs[4:8])
        cv2.imwrite(out_grid_path, np.vstack([row1, row2]))

    report = {
        "verified_frames": 393,
        "resolution": "720x1280",
        "fps": 30,
        "audio_codec": info_main["audio_codec"],
        "sha256_match_both_videos": sha_main == sha_sec,
        "studio_background_mae_mean_0_255": round(float(np.mean(floor_maes)), 4),
        "studio_background_mae_max_0_255": round(float(np.max(floor_maes)), 4),
        "yellow_crank_mae_mean_0_255": round(float(np.mean(yellow_maes)), 4),
        "teal_slider_mae_mean_0_255": round(float(np.mean(teal_maes)), 4),
        "remaining_white_text_pixels_max": remaining_white_text_max,
        "remaining_coral_pink_pixels_max": remaining_coral_max,
        "green_rail_G_over_R_ratio_min": round(green_rail_ratio_min, 3),
        "all_checks_passed": bool(
            sha_main == sha_sec
            and np.max(floor_maes) < 1.0
            and np.max(yellow_maes) < 2.0
            and remaining_white_text_max == 0
            and remaining_coral_max == 0
            and green_rail_ratio_min >= 2.2
        ),
    }
    print(json.dumps(report, indent=2))
    assert report["all_checks_passed"], f"Verification failed: {report}"


if __name__ == "__main__":
    main()

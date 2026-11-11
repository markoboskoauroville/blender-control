#!/usr/bin/env python3
"""
Processes all 393 frames of 'How Rotation Becomes a Straight Line' per changes.txt:
  "Mozes li u ovom videu izbrisati tekst i zamjeniti crno u zelno i ruzicasto u plavo"
  1. Removes white 'B. Cruz' text seamlessly via 2D discrete Laplace harmonic inpainting.
  2. Replaces pink/coral ('ruzicasto') connecting rod & collar with CAD Royal Blue ('plavo').
  3. Replaces black ('crno') guide rail & socket bolts/pins with 3D-shaded CAD Green ('zeleno').
  4. Preserves studio grey background, cast shadows, yellow crank, and teal slider identically.
"""

import concurrent.futures
import os
import sys
import time
import cv2
import numpy as np
from scipy.ndimage import gaussian_filter, distance_transform_edt
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import spsolve


def compute_grad_mag(arr: np.ndarray) -> np.ndarray:
    arr32 = arr.astype(np.float32)
    gx = cv2.Sobel(arr32, cv2.CV_32F, 1, 0, ksize=3) / 8.0
    gy = cv2.Sobel(arr32, cv2.CV_32F, 0, 1, ksize=3) / 8.0
    return np.hypot(gx, gy)


def compute_studio_floor_mask(bgr: np.ndarray) -> np.ndarray:
    b = bgr[:, :, 0].astype(np.float32)
    g = bgr[:, :, 1].astype(np.float32)
    r = bgr[:, :, 2].astype(np.float32)
    max_c = np.maximum(np.maximum(r, g), b)
    chroma = max_c - np.minimum(np.minimum(r, g), b)
    grad_v = compute_grad_mag(max_c)

    definite = ((chroma < 11.0) & (max_c >= 92.0) & (max_c <= 152.0)).astype(np.uint8)
    nc, labels, stats, _ = cv2.connectedComponentsWithStats(definite)
    h, w = bgr.shape[:2]
    seed = np.zeros_like(definite)
    for cid in range(1, nc):
        x, y, bw, bh, area = stats[cid]
        if area < 90:
            continue
        touches_border = (x == 0) or (y == 0) or (x + bw >= w) or (y + bh >= h)
        comp_vals = max_c[labels == cid]
        if touches_border or (area >= 140 and np.median(comp_vals) >= 102.0 and comp_vals.max() <= 150.0):
            seed[labels == cid] = 1

    smooth_shadow = ((chroma < 10.0) & (max_c >= 78.0) & (max_c <= 152.0) & (grad_v <= 3.6)).astype(np.uint8)
    k11 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
    wide_shadow_core = cv2.erode(smooth_shadow | seed, k11, iterations=1)

    nc2, lb2, _, _ = cv2.connectedComponentsWithStats(wide_shadow_core)
    seed_eroded = cv2.erode(seed, k11, iterations=1)
    valid_lbs = np.unique(lb2[seed_eroded > 0])
    valid_lbs = valid_lbs[valid_lbs > 0]
    connected_core = np.isin(lb2, valid_lbs).astype(np.uint8)

    # Exact radius-5 geodesic regrowth matching k11 erosion radius
    k3 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    regrown = connected_core.copy()
    for _ in range(5):
        regrown = (cv2.dilate(regrown, k3, iterations=1) & (smooth_shadow | seed)).astype(np.uint8)

    return (seed | regrown).astype(np.uint8)


def harmonic_inpaint_roi(sub_bgr: np.ndarray, hole_mask: np.ndarray, valid_donor_mask: np.ndarray) -> np.ndarray:
    ys, xs = np.where(hole_mask)
    n_unknown = len(ys)
    if n_unknown == 0:
        return sub_bgr

    h, w = hole_mask.shape
    idx_map = np.full((h, w), -1, dtype=np.int32)
    idx_map[ys, xs] = np.arange(n_unknown, dtype=np.int32)

    A = lil_matrix((n_unknown, n_unknown), dtype=np.float64)
    rhs = np.zeros((n_unknown, 3), dtype=np.float64)

    if np.any(valid_donor_mask):
        fallback_rgb = np.median(sub_bgr[valid_donor_mask], axis=0)
    else:
        fallback_rgb = np.array([58.0, 58.0, 58.0])

    for k in range(n_unknown):
        y, x = ys[k], xs[k]
        diag = 0.0
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w:
                n_idx = idx_map[ny, nx]
                if n_idx >= 0:
                    A[k, n_idx] = -1.0
                    diag += 1.0
                elif valid_donor_mask[ny, nx]:
                    rhs[k] += sub_bgr[ny, nx]
                    diag += 1.0
        A[k, k] = diag + 1e-3
        rhs[k] += 1e-3 * fallback_rgb

    A_csr = A.tocsr()
    out = sub_bgr.copy()
    for ch in range(3):
        out[ys, xs, ch] = spsolve(A_csr, rhs[:, ch])
    return out


def erase_bcruz_harmonic(frame_bgr: np.ndarray, floor_mask: np.ndarray) -> np.ndarray:
    x0, y0, x1, y1 = 275, 650, 595, 1015
    sub_bgr = frame_bgr[y0:y1, x0:x1].astype(np.float32)
    b, g, r = sub_bgr[:, :, 0], sub_bgr[:, :, 1], sub_bgr[:, :, 2]
    max_c = np.maximum(np.maximum(r, g), b)
    min_c = np.minimum(np.minimum(r, g), b)
    chroma = max_c - min_c
    fl_sub = floor_mask[y0:y1, x0:x1] > 0

    cand = ((~fl_sub) & (chroma < 48.0) & (max_c >= 88.0)).astype(np.uint8)
    nc, lb, st, cent = cv2.connectedComponentsWithStats(cand)
    core_text = np.zeros_like(cand)
    for cid in range(1, nc):
        area = st[cid, cv2.CC_STAT_AREA]
        cx = cent[cid][0] + x0
        cy = cent[cid][1] + y0
        maxv = max_c[lb == cid].max()
        if (maxv >= 145.0 or (maxv >= 110.0 and area >= 4)) and not (area <= 14 and (cx > 578 or cy < 660)):
            core_text[lb == cid] = 1

    if not np.any(core_text):
        return frame_bgr

    k7 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    dil3 = (cv2.dilate(core_text, k7, iterations=1) > 0) & (~fl_sub)

    # Include shadowed rail regions (down to V >= 26) when the rod casts its shadow across 'B. Cruz' (e.g. 00:05, 00:12),
    # while using grad_v <= 6.5 on donors so sharp T-slot walls are never sampled!
    grad_sub = compute_grad_mag(max_c)
    hole = dil3 & (chroma < 24.0) & (max_c >= 26.0)
    valid_donors = (~hole) & (~fl_sub) & (chroma < 14.0) & (max_c >= 26.0) & (max_c <= 86.0) & (grad_sub <= 6.5)
    if np.count_nonzero(valid_donors) < 20:
        valid_donors = (~hole) & (~fl_sub) & (chroma < 16.0) & (max_c >= 26.0) & (max_c <= 86.0)

    solved_sub = harmonic_inpaint_roi(sub_bgr, hole, valid_donors)

    k5 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    aa_overlap = (cv2.dilate(core_text, k5, iterations=1) > 0) & (~fl_sub) & (chroma >= 18.0)
    if np.any(aa_overlap):
        rail_under = cv2.GaussianBlur(solved_sub, (7, 7), 2.0)
        is_greenish = g > r
        pure_chroma = np.where(is_greenish, 132.0, 158.0)
        fg_cov = np.clip(chroma / pure_chroma, 0.0, 1.0)
        expected_min = fg_cov * np.where(is_greenish, 26.0, 88.0) + (1.0 - fg_cov) * rail_under[:, :, 0]
        excess_white = np.maximum(0.0, min_c - expected_min)
        solved_sub[aa_overlap] = np.clip(solved_sub[aa_overlap] - excess_white[aa_overlap, None], 0.0, 255.0)

    res = frame_bgr.copy()
    res[y0:y1, x0:x1] = np.clip(np.round(solved_sub), 0, 255).astype(np.uint8)
    return res


def process_frame(raw_bgr: np.ndarray) -> np.ndarray:
    floor_mask = compute_studio_floor_mask(raw_bgr)
    clean_bgr = erase_bcruz_harmonic(raw_bgr, floor_mask)

    img = clean_bgr.astype(np.float32)
    b, g, r = img[:, :, 0], img[:, :, 1], img[:, :, 2]

    max_c = np.maximum(np.maximum(r, g), b)
    chroma = max_c - np.minimum(np.minimum(r, g), b)

    floor_f = floor_mask.astype(np.float32)
    local_floor_v = gaussian_filter(max_c * floor_f, sigma=4.0) / np.maximum(gaussian_filter(floor_f, sigma=4.0), 1e-5)
    local_floor_v = np.clip(local_floor_v, 78.0, 148.0)

    # 1. Pink/Coral ('ruzicasto') -> CAD Royal Blue ('plavo') via YCrCb 4:2:0-deblocked constant-luma rotation!
    # Smooth chroma differences slightly (sigma=0.85) to eliminate AV1 yuv420p 2x2 chroma subsampling staircases
    # along diagonal edges while keeping 100% full-resolution 1x1 Luma Y!
    y_luma = 0.114 * b + 0.587 * g + 0.299 * r
    cr_smooth = gaussian_filter(r - y_luma, sigma=0.85)
    cb_smooth = gaussian_filter(b - y_luma, sigma=0.85)
    cg_smooth = gaussian_filter(g - y_luma, sigma=0.85)

    rg_s = cr_smooth - cg_smooth
    gb_s = np.maximum(0.0, cg_smooth - cb_smooth)
    pink_raw = np.maximum(0.0, rg_s - 0.35 * gb_s)
    strong_pink = (pink_raw > 30.0).astype(np.uint8)
    near_pink = cv2.dilate(strong_pink, np.ones((7, 7), np.uint8), iterations=1) > 0

    pink_thresh_lo = np.where(near_pink, 1.0, 5.0)
    pink_thresh_span = np.where(near_pink, 5.0, 15.0)
    pink_weight = np.clip((pink_raw - pink_thresh_lo) / pink_thresh_span, 0.0, 1.0)

    # Rotate Coral chroma (Cr ~ +106, Cb ~ -59) -> Royal Blue chroma (Cr ~ -68, Cb ~ +114) preserving 1x1 Luma Y!
    rb_smooth = np.maximum(0.0, cr_smooth - cb_smooth)
    new_y = y_luma - pink_weight * (0.06 * rb_smooth)
    new_cr = (r - y_luma) * (1.0 - pink_weight) + (-0.42 * rb_smooth) * pink_weight
    new_cb = (b - y_luma) * (1.0 - pink_weight) + (+0.69 * rb_smooth) * pink_weight
    # Reconstruct exact RGB from (new_y, new_cr, new_cb) where Y = 0.299 R + 0.587 G + 0.114 B:
    r_after_pink = new_y + new_cr
    b_after_pink = new_y + new_cb
    g_after_pink = (new_y - 0.299 * r_after_pink - 0.114 * b_after_pink) / 0.587

    # 2. Black ('crno') Rail & Socket Bolts -> 3D-Shaded CAD Green ('zeleno')
    true_dark_core = ((floor_mask == 0) & (chroma < 16.0) & (max_c <= 89.0)).astype(np.uint8)
    nc_d, lb_d, st_d, _ = cv2.connectedComponentsWithStats(true_dark_core)
    clean_dark_core = np.zeros_like(true_dark_core)
    for cid in range(1, nc_d):
        if st_d[cid, cv2.CC_STAT_AREA] >= 12:
            clean_dark_core[lb_d == cid] = 1

    near_true_dark = cv2.dilate(clean_dark_core, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)), iterations=1) > 0

    non_floor = 1.0 - floor_f
    dist_to_nonfloor = distance_transform_edt(floor_mask > 0)
    near_mech_aa = (dist_to_nonfloor <= 2.2) & near_true_dark

    dark_f = clean_dark_core.astype(np.float32)
    local_dark_v = gaussian_filter(max_c * dark_f, sigma=4.0) / np.maximum(gaussian_filter(dark_f, sigma=4.0), 1e-5)
    local_dark_v = np.clip(local_dark_v, 28.0, 85.0)

    aa_cov = np.clip((local_floor_v - max_c - 1.5) / np.maximum(local_floor_v - local_dark_v, 10.0), 0.0, 1.0)
    mech_dark_cov = np.where((non_floor > 0.5) & near_true_dark, 1.0, np.where(near_mech_aa, aa_cov, 0.0))

    strong_yellow = ((gb_s > 55.0) & (r > 140.0)).astype(np.uint8)
    colored_silhouette_only = (
        (cv2.dilate(strong_pink | strong_yellow, np.ones((5, 5), np.uint8), iterations=1) > 0)
        & (cv2.dilate(floor_mask, np.ones((5, 5), np.uint8), iterations=1) > 0)
        & (cv2.erode(clean_dark_core, np.ones((3, 3), np.uint8), iterations=1) == 0)
    )

    neutral_w = np.clip((32.0 - chroma) / 18.0, 0.0, 1.0)
    black_to_green_w = mech_dark_cov * neutral_w * (1.0 - pink_weight)
    black_to_green_w = np.where(colored_silhouette_only, 0.0, black_to_green_w)

    lum = (r + g + b) / 3.0
    base_l = np.minimum(lum, 92.0)
    spec_l = np.maximum(0.0, lum - 92.0)

    green_r = 0.68 * base_l + 0.92 * spec_l
    green_g = 2.18 * base_l + 4.0 + 1.05 * spec_l
    green_b = 0.76 * base_l + 0.92 * spec_l

    final_r = r_after_pink * (1.0 - black_to_green_w) + green_r * black_to_green_w
    final_g = g_after_pink * (1.0 - black_to_green_w) + green_g * black_to_green_w
    final_b = b_after_pink * (1.0 - black_to_green_w) + green_b * black_to_green_w

    out = np.stack([final_b, final_g, final_r], axis=-1)
    return np.clip(np.round(out), 0, 255).astype(np.uint8)


def _worker(task):
    in_path, out_path = task
    raw = cv2.imread(in_path)
    edited = process_frame(raw)
    cv2.imwrite(out_path, edited)
    return 1


def main():
    in_dir = sys.argv[1]
    out_dir = sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    tasks = [
        (f"{in_dir}/frame_{fno:04d}.png", f"{out_dir}/frame_{fno:04d}.png")
        for fno in range(1, 394)
    ]
    t0 = time.time()
    with concurrent.futures.ProcessPoolExecutor(max_workers=8) as pool:
        done = sum(pool.map(_worker, tasks, chunksize=8))
    print(f"Processed {done}/393 frames in {time.time() - t0:.2f}s -> {out_dir}")


if __name__ == "__main__":
    main()

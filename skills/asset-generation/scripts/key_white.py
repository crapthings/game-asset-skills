# /// script
# requires-python = ">=3.11,<3.14"
# dependencies = [
#     "numpy>=2,<3",
#     "opencv-python-headless>=4.10,<5",
#     "pillow>=11,<13",
#     "pymatting>=1.1.14,<2",
#     "scipy>=1.13,<2",
# ]
# ///
"""Prepare a green/white-background trimap or extract a transparent asset."""

import argparse
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps


# Parse the two-stage workflow and its image-space parameters.
def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image', type=Path)
    parser.add_argument('output', type=Path, help='New PNG path; existing files are never overwritten.')
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare', action='store_true', help='Write a draft trimap for review, not a cutout.')
    mode.add_argument('--trimap', type=Path, help='Reviewed trimap: black=background, white=foreground, gray=unknown.')
    mode.add_argument('--bleed-only', action='store_true', help='Fill transparent RGB from nearby foreground without changing alpha.')
    mode.add_argument('--clean-green', action='store_true', help='Remove green remnants and edge spill from an existing transparent PNG.')
    parser.add_argument('--green-max-area', type=int, default=64, help='Largest green component eligible for cleanup, in pixels.')
    parser.add_argument('--green-edge-radius', type=int, default=32, help='Maximum distance from a transparent pixel for green cleanup.')
    parser.add_argument('--white-threshold', type=int, default=245)
    parser.add_argument('--background', choices=('white', 'green'), default='white')
    parser.add_argument('--green-difference', type=int, default=60, help='Minimum G - max(R, B) for green background seeds.')
    parser.add_argument('--radius', type=int, default=3, help='Unknown boundary radius in original-image pixels.')
    args = parser.parse_args()
    if not 1 <= args.white_threshold <= 255 or args.radius < 1:
        parser.error('Threshold must be 1..255 and radius must be positive.')
    if args.output.suffix.lower() != '.png':
        parser.error('Output must be PNG.')
    if not 1 <= args.green_difference <= 255:
        parser.error('Green difference must be 1..255.')
    if args.green_max_area < 1 or args.green_edge_radius < 1:
        parser.error('Green component area and edge radius must be positive.')
    return args


# Load an opaque RGB source with its displayed orientation applied.
def load_source(path):
    with Image.open(path) as source:
        source = ImageOps.exif_transpose(source).convert('RGBA')
        rgba = np.asarray(source)
    if np.any(rgba[:, :, 3] != 255):
        raise ValueError('Source already contains transparency; use the opaque master.')
    return rgba[:, :, :3].copy()


# Identify near-white regions connected to any canvas border.
def border_background(rgb, threshold):
    candidates = (np.min(rgb, axis=2) >= threshold).astype(np.uint8)
    _, labels = cv2.connectedComponents(candidates, connectivity=8)
    border_labels = np.unique(np.concatenate((labels[0], labels[-1], labels[:, 0], labels[:, -1])))
    border_labels = border_labels[border_labels != 0]
    return np.isin(labels, border_labels)


# Build a conservative draft whose uncertain boundary must be reviewed before extraction.
def make_trimap(rgb, threshold, radius, background_color='white', green_difference=60):
    if background_color == 'green':
        channels = rgb.astype(np.int16)
        background = channels[:, :, 1] - np.maximum(channels[:, :, 0], channels[:, :, 2]) >= green_difference
    else:
        background = border_background(rgb, threshold)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * radius + 1,) * 2)
    foreground = (~background).astype(np.uint8)
    core = cv2.erode(foreground, kernel, borderType=cv2.BORDER_CONSTANT, borderValue=0) > 0
    outer = cv2.dilate(foreground, kernel) > 0
    trimap = np.full(background.shape, 128, dtype=np.uint8)
    trimap[~outer] = 0
    trimap[core] = 255
    return trimap


# Reject trimaps that cannot constrain foreground and background estimation.
def validate_trimap(trimap, shape):
    if trimap.shape != shape:
        raise ValueError('Trimap dimensions must match the oriented source image.')
    if not np.any(trimap == 0) or not np.any(trimap == 255):
        raise ValueError('Trimap needs both pure black background and pure white foreground seeds.')


# Reserve a new destination without replacing a master or an existing derivative.
def save_png(array, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        Image.fromarray(array).save(stream, format='PNG')
    print(path)


# Estimate soft alpha and uncontaminated foreground colors from the reviewed trimap.
def extract(rgb, trimap):
    from pymatting import estimate_alpha_cf, estimate_foreground_ml

    image = rgb.astype(np.float64) / 255.0
    alpha = estimate_alpha_cf(image, trimap.astype(np.float64) / 255.0)
    foreground = estimate_foreground_ml(image, alpha)
    rgba = np.dstack((foreground, alpha))
    return np.rint(np.clip(rgba, 0, 1) * 255).astype(np.uint8)


# Fill fully transparent texels with nearby solid foreground colors to reduce filtering fringes.
def bleed_transparent(rgba):
    from scipy.ndimage import distance_transform_edt

    solid = rgba[:, :, 3] >= 250
    if not np.any(solid):
        raise ValueError('Color bleeding requires at least one nearly opaque foreground pixel.')
    result = rgba.copy()
    transparent = rgba[:, :, 3] == 0
    indices = distance_transform_edt(~solid, return_distances=False, return_indices=True)
    result[transparent, :3] = rgba[indices[0][transparent], indices[1][transparent], :3]
    return result


# Map a value interval to a smooth zero-to-one transition.
def smoothstep(low, high, values):
    t = np.clip((values - low) / (high - low), 0, 1)
    return t * t * (3 - 2 * t)


# Decode sRGB image colors before measuring green contamination.
def linear_colors(rgba):
    srgb = rgba[:, :, :3].astype(np.float64) / 255.0
    return np.where(srgb <= 0.04045, srgb / 12.92, ((srgb + 0.055) / 1.055) ** 2.4)


# Encode a linear color channel back into an eight-bit sRGB image channel.
def encode_channel(channel):
    srgb = np.where(channel <= 0.0031308, channel * 12.92, 1.055 * np.maximum(channel, 0) ** (1 / 2.4) - 0.055)
    return np.rint(np.clip(srgb, 0, 1) * 255).astype(np.uint8)


# Suppress excess green only within a narrow transparent boundary while keeping alpha unchanged.
def despill_green_edges(rgba):
    from scipy.ndimage import distance_transform_edt

    transparent = rgba[:, :, 3] < 16
    if not np.any(transparent):
        return rgba.copy()
    edge = (distance_transform_edt(~transparent) <= 4) | (rgba[:, :, 3] < 250)
    linear = linear_colors(rgba)
    rb = np.maximum(linear[:, :, 0], linear[:, :, 2])
    excess = np.maximum(0, linear[:, :, 1] - rb)
    weight = edge * smoothstep(0.01, 0.08, excess)
    result = rgba.copy()
    result[:, :, 1] = encode_channel(linear[:, :, 1] - weight * excess)
    return result


# Remove only small saturated green components close to the transparent silhouette.
def clean_green_remnants(rgba, max_area=64, edge_radius=32):
    from scipy.ndimage import distance_transform_edt

    linear = linear_colors(rgba)
    rb = np.maximum(linear[:, :, 0], linear[:, :, 2])
    excess = np.maximum(0, linear[:, :, 1] - rb)
    key = smoothstep(0.08, 0.3, excess) * (1 - smoothstep(0.02, 0.08, rb))
    candidates = ((key > 0.01) & (rgba[:, :, 3] > 0)).astype(np.uint8)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(candidates, connectivity=8)
    eligible = np.zeros(count, dtype=bool)
    eligible[1:] = stats[1:, cv2.CC_STAT_AREA] <= max_area
    transparent = rgba[:, :, 3] < 16
    if not np.any(transparent):
        return rgba.copy()
    near_edge = distance_transform_edt(~transparent) <= edge_radius
    selected = eligible[labels] & near_edge
    weight = np.where(selected, key, 0)
    result = rgba.copy()
    green = linear[:, :, 1] * (1 - weight) + np.minimum(linear[:, :, 1], rb) * weight
    result[:, :, 1] = encode_channel(green)
    result[:, :, 3] = np.rint(rgba[:, :, 3] * (1 - weight * smoothstep(0.18, 0.5, excess))).astype(np.uint8)
    print(f'Green-remnant cleanup: {np.count_nonzero(selected)} candidate pixels.')
    return result


# Composite straight-alpha pixels onto a solid background for edge inspection.
def composite(rgba, color):
    alpha = rgba[:, :, 3:4].astype(np.float64) / 255.0
    return np.rint(rgba[:, :, :3] * alpha + np.asarray(color) * (1 - alpha)).astype(np.uint8)


# Run preparation or extraction and write three full-resolution background checks.
def main():
    args = parse_args()
    transparent_input = args.bleed_only or args.clean_green
    rgb = None if transparent_input else load_source(args.image)
    if args.prepare:
        trimap = make_trimap(rgb, args.white_threshold, args.radius, args.background, args.green_difference)
        validate_trimap(trimap, rgb.shape[:2])
        save_png(trimap, args.output)
        print('Review this draft: protect clothing matching the background, check enclosed gaps, and keep mixed edges gray.')
        return
    if not transparent_input:
        with Image.open(args.trimap) as source:
            trimap = np.asarray(ImageOps.exif_transpose(source).convert('L'))
        validate_trimap(trimap, rgb.shape[:2])
    backgrounds = {'black': (0, 0, 0), 'gray': (128, 128, 128), 'color': (55, 100, 160)}
    checks = {name: args.output.with_name(f'{args.output.stem}-check-{name}.png') for name in backgrounds}
    for path in (args.output, *checks.values()):
        if path.exists():
            raise FileExistsError(f'Output already exists: {path}')
    if transparent_input:
        with Image.open(args.image) as source:
            rgba = np.asarray(ImageOps.exif_transpose(source).convert('RGBA'))
    else:
        rgba = extract(rgb, trimap)
    if args.clean_green or (not transparent_input and args.background == 'green'):
        rgba = clean_green_remnants(rgba, args.green_max_area, args.green_edge_radius)
        rgba = despill_green_edges(rgba)
    rgba = bleed_transparent(rgba)
    save_png(rgba, args.output)
    for name, color in backgrounds.items():
        save_png(composite(rgba, color), checks[name])


# Execute the command-line workflow only when this file is run directly.
if __name__ == '__main__':
    main()

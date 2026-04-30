"""
extract_frames.py — Video frame extractor for paper figures
Supports iPhone timelapse (real-time remapping) and normal videos.

━━ NORMAL VIDEO ━━
    python extract_frames.py video.mp4 --interval 0.5
    python extract_frames.py video.mp4 --timestamps 0 0.5 1.0 1.5 2.0 37.5

━━ iPHONE TIMELAPSE — specify real-world timestamps ━━
    python extract_frames.py timelapse.mp4 --real-duration 120 --interval 5
    python extract_frames.py timelapse.mp4 --speedup 10 --interval 5
    python extract_frames.py timelapse.mp4 --real-duration 120 --timestamps 0 10 20 30 60 90
    python extract_frames.py timelapse.mp4 --timelapse --interval 5

━━ GRID OUTPUT ━━
    python extract_frames.py video.mp4 --interval 0.5 --grid
    python extract_frames.py video.mp4 --interval 0.5 --grid --cols 3

Options:
    --interval SECS       Extract one frame every N real seconds (default: 1.0)
    --timestamps T ...    Exact real-world timestamps (overrides --interval)
    --start SECS          Real start time in seconds (default: 0)
    --end SECS            Real end time in seconds (default: end)
    --output DIR          Output folder (default: frames_<videoname>)
    --grid                Also produce a combined grid image (auto-wraps, default 4 cols)
    --cols N              Grid columns (default: 4)
    --label-color         white or black (default: white)
    --no-label            Skip timestamp overlay
    --label-pos           tl tr bl br (default: tl)
    --font-scale F        Font size multiplier (~12%% image height = 1.0, default: 1.0)
    --bg-opacity N        Background box opacity 0–255 (default: 140)
    --padding PX          Gap between grid frames in pixels (default: 8)

  Timelapse options:
    --real-duration SECS  Actual real-world recording length in seconds
    --speedup FACTOR      Speed-up multiplier (e.g. 10 means 10x faster)
    --timelapse           Auto-detect speedup from video metadata (ffprobe)
"""

import cv2
import sys
import argparse
import math
import subprocess
import json
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ── iPhone timelapse reference table ─────────────────────────────────────────
IPHONE_TIMELAPSE_SPEEDUP = [
    (10,   6),
    (20,   10),
    (40,   20),
    (80,   40),
    (160,  80),
    (320,  160),
    (float('inf'), 1800),
]

def iphone_speedup_from_real_duration(real_secs: float) -> int:
    real_mins = real_secs / 60
    for threshold_min, factor in IPHONE_TIMELAPSE_SPEEDUP:
        if real_mins < threshold_min:
            return factor
    return IPHONE_TIMELAPSE_SPEEDUP[-1][1]

# ── font loader ───────────────────────────────────────────────────────────────

def load_font(size: int) -> ImageFont.FreeTypeFont:
    """
    Try Helvetica first, then Arial (Windows), then Liberation Sans (Linux).
    Falls back to PIL's built-in bitmap font if nothing is found.
    """
    candidates = [
        # macOS
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/Library/Fonts/Helvetica.ttf",
        # Windows — Arial is metrically near-identical to Helvetica
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/Arial.ttf",
        # Linux
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "/usr/share/fonts/opentype/urw-base35/NimbusSans-Regular.otf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    # last resort: PIL default (small, no sizing)
    print("  Warning: no Helvetica/Arial found — using PIL default font.")
    return ImageFont.load_default()

# ── helpers ───────────────────────────────────────────────────────────────────

def format_ts(seconds: float) -> str:
    if seconds >= 60:
        m = int(seconds) // 60
        s = seconds - m * 60
        if s == 0:
            return f"{m}min"
        s_str = f"{s:.1f}".rstrip('0').rstrip('.')
        return f"{m}min {s_str}s"
    if seconds == int(seconds):
        return f"{int(seconds)}s"
    return f"{seconds:.2f}".rstrip('0').rstrip('.') + "s"


def draw_label(img_bgr, label: str, position: str,
               color_rgb: tuple, scale: float, bg_opacity: int):
    """
    Render a timestap label onto a frame using PIL:
      • Helvetica / Arial font
      • Semi-transparent black background box
    Accepts and returns a BGR numpy array (OpenCV format).
    """
    h, w = img_bgr.shape[:2]

    # ── font size: ~12% of image height × user scale ──────────────────────
    font_size = max(12, int(h * 0.12 * scale))
    font = load_font(font_size)

    margin = int(h * 0.03)           # 3% of height from edge
    pad_x  = int(font_size * 0.35)   # horizontal padding inside box
    pad_y  = int(font_size * 0.20)   # vertical padding inside box

    # ── measure text ─────────────────────────────────────────────────────
    dummy_img  = Image.new("RGBA", (1, 1))
    dummy_draw = ImageDraw.Draw(dummy_img)
    bbox = dummy_draw.textbbox((0, 0), label, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    # ── calculate text origin (top-left of text) ──────────────────────────
    box_w = tw + pad_x * 2
    box_h = th + pad_y * 2

    if position == "tl":
        bx, by = margin, margin
    elif position == "tr":
        bx, by = w - box_w - margin, margin
    elif position == "bl":
        bx, by = margin, h - box_h - margin
    elif position == "br":
        bx, by = w - box_w - margin, h - box_h - margin
    else:
        bx, by = margin, margin

    tx = bx + pad_x - bbox[0]
    ty = by + pad_y - bbox[1]

    # ── composite onto frame using PIL RGBA ───────────────────────────────
    img_rgb  = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    pil_base = Image.fromarray(img_rgb).convert("RGBA")

    # semi-transparent black box
    overlay = Image.new("RGBA", pil_base.size, (0, 0, 0, 0))
    draw    = ImageDraw.Draw(overlay)
    draw.rectangle(
        [bx, by, bx + box_w, by + box_h],
        fill=(0, 0, 0, bg_opacity)
    )
    # text on top (fully opaque)
    draw.text((tx, ty), label, font=font, fill=(*color_rgb, 255))

    composited = Image.alpha_composite(pil_base, overlay).convert("RGB")
    return cv2.cvtColor(np.array(composited), cv2.COLOR_RGB2BGR)


# ── ffprobe timelapse detection ───────────────────────────────────────────────

def try_ffprobe_speedup(video_path: Path):
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_streams", "-show_format", str(video_path)],
            capture_output=True, text=True, timeout=10
        )
        data = json.loads(result.stdout)
        for stream in data.get("streams", []):
            if stream.get("codec_type") != "video":
                continue
            tags = stream.get("tags", {})
            capture_us = tags.get("com.apple.quicktime.camera.framereadouttimeinmicroseconds")
            if capture_us:
                capture_fps = 1_000_000 / float(capture_us)
                num, den = stream.get("r_frame_rate", "30/1").split("/")
                output_fps = float(num) / float(den)
                return output_fps / capture_fps
            avg_str = stream.get("avg_frame_rate", "")
            r_str   = stream.get("r_frame_rate", "")
            if avg_str and r_str and "/" in avg_str and "/" in r_str:
                a_num, a_den = avg_str.split("/")
                r_num, r_den = r_str.split("/")
                avg_fps = float(a_num) / float(a_den) if float(a_den) else 0
                r_fps   = float(r_num) / float(r_den) if float(r_den) else 0
                if avg_fps > 0 and r_fps > avg_fps * 1.5:
                    return r_fps / avg_fps
        return None
    except Exception:
        return None

# ── core extraction ───────────────────────────────────────────────────────────

def extract(args):
    video_path = Path(args.video)
    if not video_path.exists():
        sys.exit(f"Error: file not found: {video_path}")

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        sys.exit(f"Error: could not open video: {video_path}")

    fps          = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    video_dur    = total_frames / fps

    # ── resolve speed-up factor ──────────────────────────────────────────────
    speedup = 1.0

    if args.real_duration:
        speedup  = args.real_duration / video_dur
        real_dur = args.real_duration
        print(f"Mode: timelapse  |  speedup = {speedup:.1f}×  "
              f"(video {video_dur:.1f}s → real {real_dur:.1f}s)")
    elif args.speedup:
        speedup  = args.speedup
        real_dur = video_dur * speedup
        print(f"Mode: timelapse  |  speedup = {speedup:.1f}×  "
              f"(video {video_dur:.1f}s → real {real_dur:.1f}s)")
    elif args.timelapse:
        detected = try_ffprobe_speedup(video_path)
        if detected:
            speedup  = detected
            real_dur = video_dur * speedup
            print(f"Mode: timelapse (auto-detected)  |  speedup = {speedup:.1f}×  "
                  f"(video {video_dur:.1f}s → real {real_dur:.1f}s)")
        else:
            print("Warning: could not auto-detect speedup. Falling back to normal mode.")
            real_dur = video_dur
    else:
        real_dur = video_dur
        print(f"Mode: normal video  |  {video_dur:.2f}s  |  {fps:.1f} fps")

    print(f"Video: {video_path.name}  |  {total_frames} frames  |  {fps:.1f} fps")

    # ── build timestamp list (real time) ─────────────────────────────────────
    if args.timestamps:
        real_targets = sorted(float(t) for t in args.timestamps)
    else:
        start = args.start if args.start is not None else 0.0
        end   = min(args.end if args.end is not None else real_dur, real_dur)
        real_targets, t = [], start
        while t <= end + 1e-6:
            real_targets.append(round(t, 6))
            t += args.interval
        real_targets = [t for t in real_targets if t <= end + 1e-6]

    print(f"Extracting {len(real_targets)} frames: {[format_ts(t) for t in real_targets]}")

    # ── output dir ───────────────────────────────────────────────────────────
    out_dir = Path(args.output) if args.output else Path(f"frames_{video_path.stem}")
    out_dir.mkdir(parents=True, exist_ok=True)

    color_rgb = (0, 0, 0) if args.label_color == "black" else (255, 255, 255)

    saved_paths = []
    for real_ts in real_targets:
        video_ts = real_ts / speedup
        frame_no = min(max(int(video_ts * fps), 0), total_frames - 1)

        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_no)
        ret, frame = cap.read()
        if not ret:
            print(f"  Warning: could not read frame at {format_ts(real_ts)}, skipping.")
            continue

        if not args.no_label:
            frame = draw_label(frame, format_ts(real_ts), args.label_pos,
                               color_rgb, args.font_scale, args.bg_opacity)

        fname = out_dir / f"frame_{real_ts:.2f}s.png"
        cv2.imwrite(str(fname), frame)
        saved_paths.append(fname)
        print(f"  [{format_ts(real_ts):>10}]  video@{video_ts:.2f}s  →  {fname.name}")

    cap.release()

    if args.grid and saved_paths:
        make_grid(saved_paths, out_dir, args)

    print(f"\nDone. {len(saved_paths)} frames → {out_dir.resolve()}")

# ── grid compositor ───────────────────────────────────────────────────────────

def make_grid(frame_paths, out_dir, args):
    n   = len(frame_paths)
    # Default: 4 columns → auto-wraps to multiple rows
    cols = args.cols if args.cols else min(n, 4)
    rows = math.ceil(n / cols)
    pad  = args.padding

    imgs     = [Image.open(p) for p in frame_paths]
    fw, fh   = imgs[0].size
    grid_w   = cols * fw + (cols + 1) * pad
    grid_h   = rows * fh + (rows + 1) * pad

    grid = Image.new("RGB", (grid_w, grid_h), (255, 255, 255))
    for idx, img in enumerate(imgs):
        r, c = divmod(idx, cols)
        x = pad + c * (fw + pad)
        y = pad + r * (fh + pad)
        grid.paste(img, (x, y))

    grid_path = out_dir / "grid.png"
    grid.save(str(grid_path), dpi=(300, 300))
    print(f"  Grid: {cols} cols × {rows} rows  |  {grid_w}×{grid_h}px  →  {grid_path.name}")

# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(
        description="Extract timestamped frames from a video (supports iPhone timelapse).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("video", help="Input video file")

    p.add_argument("--interval",      type=float, default=1.0,
                   help="Frame every N real seconds (default: 1.0)")
    p.add_argument("--timestamps",    type=float, nargs="+", metavar="T",
                   help="Specific real-world timestamps in seconds (overrides --interval)")
    p.add_argument("--start",         type=float, default=None)
    p.add_argument("--end",           type=float, default=None)

    tl = p.add_argument_group("timelapse (iPhone / time-remapped video)")
    tl.add_argument("--real-duration", type=float, default=None, metavar="SECS")
    tl.add_argument("--speedup",       type=float, default=None, metavar="FACTOR")
    tl.add_argument("--timelapse",     action="store_true")

    p.add_argument("--output",        type=str, default=None)
    p.add_argument("--grid",          action="store_true",
                   help="Generate a combined grid image")
    p.add_argument("--cols",          type=int, default=None,
                   help="Grid columns (default: 4, auto-wraps to multiple rows)")
    p.add_argument("--label-color",   choices=["white", "black"], default="white")
    p.add_argument("--no-label",      action="store_true")
    p.add_argument("--label-pos",     choices=["tl", "tr", "bl", "br"], default="tl")
    p.add_argument("--font-scale",    type=float, default=1.0,
                   help="Font size multiplier (1.0 = ~12%% image height, default: 1.0)")
    p.add_argument("--bg-opacity",    type=int, default=140, metavar="0-255",
                   help="Background box opacity 0 (transparent) – 255 (solid), default: 140")
    p.add_argument("--padding",       type=int, default=8,
                   help="Pixel gap between frames in grid (default: 8)")

    args = p.parse_args()

    if sum([args.real_duration is not None, args.speedup is not None, args.timelapse]) > 1:
        p.error("Use only one of --real-duration, --speedup, --timelapse.")

    args.bg_opacity = max(0, min(255, args.bg_opacity))
    extract(args)

if __name__ == "__main__":
    main()

import cv2
import numpy as np
import subprocess
import imageio_ffmpeg
import os
import time

ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
input_video = r'C:\Users\anila\Downloads\echo-assist-ai-phase1\echo-assist-ai\backend\app\static\cane_intro_orig.mp4'
output_video = r'C:\Users\anila\Downloads\echo-assist-ai-phase1\echo-assist-ai\backend\app\static\cane_intro.mp4'

cap = cv2.VideoCapture(input_video)
fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

target_w, target_h = 1920, 1080
fit_scale = 0.65
content_h = int(target_h * fit_scale)
content_w = int(orig_w * (content_h / orig_h))
x_off = (target_w - content_w) // 2
y_off = 65

print(f'Processing {total_frames} frames: {orig_w}x{orig_h} -> {content_w}x{content_h} centered at ({x_off}, {y_off}) on {target_w}x{target_h} #06080f')

# Target background color #06080f in BGR: B=15, G=8, R=6
target_bg = np.array([15, 8, 6], dtype=np.float32)

# Start ffmpeg subprocess with pipe input
cmd = [
    ffmpeg_exe,
    '-y',
    '-loglevel', 'error',
    '-f', 'rawvideo',
    '-vcodec', 'rawvideo',
    '-s', f'{target_w}x{target_h}',
    '-pix_fmt', 'bgr24',
    '-r', str(fps),
    '-i', '-',
    '-c:v', 'libx264',
    '-pix_fmt', 'yuv420p',
    '-crf', '17',
    '-preset', 'fast',
    '-movflags', '+faststart',
    output_video
]

proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

t0 = time.time()
frame_idx = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    resized = cv2.resize(frame, (content_w, content_h), interpolation=cv2.INTER_AREA)
    bg_bgr = np.median(resized[:15, :15], axis=(0, 1))
    
    # Distance from background color
    diff = np.linalg.norm(resized.astype(np.float32) - bg_bgr, axis=2)
    
    # Soft alpha matte
    alpha = np.clip((diff - 6.0) / 14.0, 0.0, 1.0)
    alpha_3d = alpha[:, :, np.newaxis]
    
    # Color un-premultiply & blend
    fg_clean = resized.astype(np.float32) - (1.0 - alpha_3d) * bg_bgr
    fg_clean = np.clip(fg_clean, 0.0, 255.0)
    
    blended = alpha_3d * fg_clean + (1.0 - alpha_3d) * target_bg
    
    # Full 1920x1080 canvas
    canvas = np.full((target_h, target_w, 3), target_bg, dtype=np.float32)
    canvas[y_off:y_off+content_h, x_off:x_off+content_w] = blended
    
    frame_bgr = np.clip(canvas, 0, 255).astype(np.uint8)
    proc.stdin.write(frame_bgr.tobytes())
    
    frame_idx += 1
    if frame_idx % 30 == 0:
        elapsed = time.time() - t0
        print(f'Frame {frame_idx}/{total_frames} ({frame_idx/total_frames*100:.0f}%) - {elapsed:.1f}s')

cap.release()
proc.stdin.close()
proc.wait()

elapsed = time.time() - t0
print(f'Completed in {elapsed:.1f}s! Output size: {os.path.getsize(output_video)} bytes')

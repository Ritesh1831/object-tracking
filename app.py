import cv2
import tempfile
import streamlit as st
from tracker import EuclideanDistTracker
import numpy as np
import os
from datetime import datetime

# ------------------------------
# Streamlit Page Config
# ------------------------------
st.set_page_config(page_title="🚗 Object Tracking App", layout="wide")
st.title("🚗 Real-time Object Tracking with OpenCV + Streamlit")
st.markdown("Upload a video, choose options, and get a tracked output in seconds!")

# ------------------------------
# Sidebar Controls
# ------------------------------
st.sidebar.header("⚙️ Settings")
resize_width = st.sidebar.selectbox("Resize Width", [320, 480, 640], index=2)
frame_skip   = st.sidebar.slider("Frame Skip (higher = faster)", 1, 10, 3)
min_area     = st.sidebar.slider("Min Object Area", 50, 500, 100)

# ------------------------------
# File Upload
# ------------------------------
uploaded_file = st.file_uploader("Upload a video", type=["mp4", "avi", "mov"])

if uploaded_file is not None:
    tfile = tempfile.NamedTemporaryFile(delete=False)
    tfile.write(uploaded_file.read())
    video_path = tfile.name

    st.video(video_path)

    if st.button("🚀 Start Processing"):
        st.info("Processing video... please wait ⏳")
        progress = st.progress(0)

        tracker = EuclideanDistTracker()

        # MOG2 with shadow detection OFF — shadows were creating false detections
        object_detector = cv2.createBackgroundSubtractorMOG2(
            history=500, varThreshold=40, detectShadows=False
        )

        # Morphological kernels
        kernel_open  = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))   # noise removal
        kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))   # fill holes
        kernel_dilate = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))   # merge fragments

        cap = cv2.VideoCapture(video_path)
        total_video_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25

        frame_h = int(resize_width * 0.5625)
        frame_area = resize_width * frame_h
        max_area   = frame_area * 0.35    # reject blobs covering >35% of frame

        output_path = f"output_{datetime.now().strftime('%H%M%S')}.mp4"
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(output_path, fourcc, fps, (resize_width, frame_h))

        # ── Colour palette: each ID gets a consistent colour ──────────────────
        rng = np.random.default_rng(42)
        colors = [tuple(int(c) for c in rng.integers(80, 230, 3)) for _ in range(500)]

        total_objects  = 0
        frame_count    = 0
        processed_frames = 0

        # ── Warmup: feed first N frames to build background model, don't track ─
        WARMUP_FRAMES = min(60, total_video_frames // 10)
        warmup_done   = False

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame_count += 1

            frame = cv2.resize(frame, (resize_width, frame_h))

            # Feed warmup frames into background model only (no detection/tracking)
            if frame_count <= WARMUP_FRAMES:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray = cv2.GaussianBlur(gray, (5, 5), 0)
                object_detector.apply(gray, learningRate=0.1)   # fast learn during warmup
                out.write(frame)   # write original frame for warmup period
                progress.progress(min(1.0, frame_count / total_video_frames))
                continue

            # Skip frames for speed (after warmup)
            if (frame_count - WARMUP_FRAMES) % frame_skip != 0:
                continue

            # ── Pre-process frame before feeding to MOG2 ──────────────────────
            # Grayscale + Gaussian blur → reduces colour noise, sharpens motion signal
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (5, 5), 0)

            # Slow learning rate after warmup so background isn't "forgotten" fast
            mask = object_detector.apply(gray, learningRate=0.003)

            # Binary threshold (shadow pixels ~127 are already gone; removes weak edges)
            _, mask = cv2.threshold(mask, 200, 255, cv2.THRESH_BINARY)

            # Morphological pipeline
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  kernel_open)    # kill specks
            mask = cv2.dilate(mask, kernel_dilate, iterations=2)            # merge fragments
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel_close)   # fill holes

            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            detections = []
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if min_area < area < max_area:
                    x, y, w, h = cv2.boundingRect(cnt)
                    detections.append([x, y, w, h])

            # ── Track ─────────────────────────────────────────────────────────
            boxes_ids = tracker.update(detections)
            for box_id in boxes_ids:
                x, y, w, h, obj_id = box_id
                color = colors[obj_id % len(colors)]

                # Draw filled label background for readability
                label    = f"ID {obj_id}"
                (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
                lx = x;  ly = max(y - th - 6, 0)
                cv2.rectangle(frame, (lx, ly), (lx + tw + 4, ly + th + 6), color, -1)
                cv2.putText(frame, label, (lx + 2, ly + th + 2),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)

                # Draw bounding box with per-ID colour
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

                total_objects = max(total_objects, obj_id + 1)

            # Object count overlay
            cv2.putText(frame, f"Objects: {len(boxes_ids)}", (10, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 0), 2)

            out.write(frame)
            processed_frames += 1

            if total_video_frames > 0:
                progress.progress(min(1.0, frame_count / total_video_frames))

        cap.release()
        out.release()

        st.success("✅ Processing Complete!")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Frames",     str(frame_count))
        col2.metric("Processed Frames", str(processed_frames))
        col3.metric("Objects Tracked",  str(total_objects))

        st.subheader("🎥 Processed Output")
        st.video(output_path)

        with open(output_path, "rb") as f:
            st.download_button("⬇️ Download Processed Video", f, file_name="tracked_output.mp4")

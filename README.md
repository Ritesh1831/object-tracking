# 🚗 Object Tracking App

A **high-performance, user-friendly web app** for **object detection and tracking** in videos, built using **OpenCV** and **Streamlit**. Designed for speed, clarity, and real-world usability.


## 📌 Overview

This app lets you upload a video, tune tracking parameters, and generate a **processed tracking video** with **clean metrics and insights**.
No clutter. No lag. Just results.

Perfect for:

* Computer vision demos
* Academic projects
* Rapid experimentation
* Performance-focused tracking pipelines

---

## ✨ Key Features

* 🎥 **Video Upload Support**
  Supports `.mp4`, `.avi`, and `.mov` formats

* 🎛️ **Adjustable Tracking Controls**

  * Frame skipping (performance boost)
  * Resize width (memory + speed control)
  * Minimum object area filtering

* 📊 **Real-Time Progress Bar**
  Track processing status clearly

* 📈 **Post-Processing Metrics**

  * Total frames processed
  * Objects detected
  * Processing time stats

* 📥 **Download Processed Video**
  Export the final tracked output instantly

* 🧼 **Clean & Minimal UI**
  Focused on results, not distractions

---

## 🛠️ Tech Stack

* **Language**: Python 3.8+
* **Framework**: Streamlit
* **Computer Vision**: OpenCV
* **Deployment Friendly**: Local / GitHub Codespaces

---

## ⚡ Run Locally

1. Install dependencies

```bash
pip install -r requirements.txt
```

2. Start the app

```bash
streamlit run app.py
```

3. Open in browser

```text
http://localhost:8501
```

---

## 🐳 Run in GitHub Codespaces

1. Install system dependencies

```bash
sudo apt-get update && sudo apt-get install -y libgl1
```

2. Install Python requirements

```bash
pip install -r requirements.txt
```

3. Run Streamlit

```bash
streamlit run app.py --server.port 8000 --server.address 0.0.0.0
```

4. Open the **forwarded port** in your browser 🚀

---

## 🚀 Why This Version Is Faster

This release is **optimized for performance** by design:

* ❌ No live frame rendering (`st.image`)
* ✅ Shows **only the final processed video**
* ⚙️ Frame skipping + resizing = full performance control
* 📊 Lightweight metrics instead of heavy UI updates

Net result: **Less lag. Faster processing. Cleaner output.**

---

## 🎯 Ideal Use Cases

* Object tracking demos
* CV pipeline prototyping
* Academic & final-year projects
* Performance benchmarking

---

## ⭐ Final Thoughts

This app cuts the fluff and delivers **pure tracking performance**.
Fast. Clean. Production-ready.

If you like it, ⭐ the repo and ship it forward.

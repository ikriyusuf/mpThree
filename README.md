# mpThree 🎵

Premium, lightweight, and Dockerized YouTube to MP3 downloader with a stunning Apple-inspired interface.

## ✨ Features

- **🚀 High-Speed Downloads**: Optimized `yt-dlp` integration with concurrent fragment downloading.
- **📊 Real-time Progress**: Live status updates and progress bar via Server-Sent Events (SSE).
- **🍎 Apple Aesthetic**: Authentic, minimalist Apple-style interface (Apple ID/iCloud inspired).
- **🐳 Docker Ready**: Zero-configuration deployment using Docker and Docker Compose.
- **🧹 Auto-Cleaning**: Intelligent metadata processing and file sanitization.

## 🛠️ Tech Stack

- **Backend**: Python, Flask, Gunicorn
- **Core**: yt-dlp, FFmpeg
- **Frontend**: Vanilla JS, CSS3
- **Deployment**: Docker, Docker Compose

## 🚀 Quick Start (Docker)

Ensure you have [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/) installed.

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yusuf/mpThree.git
   cd mpThree
   ```

2. **Build and start**:
   ```bash
   docker-compose up --build
   ```

3. **Access the app**:
   Open [http://localhost:1966](http://localhost:1966) in your browser.

## 💻 Local Development (Windows)

If you prefer to run locally without Docker:

1. **Install FFmpeg**: Download and add it to your PATH.
2. **Install requirements**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the app**:
   ```bash
   python app.py
   ```

## 📝 Configuration

Settings are managed in `core/settings.py`, allowing you to adjust:
- Audio quality (default: 192kbps)
- Audio format (default: mp3)
- Output folders

---
*Created with ❤️ for a better music experience.*

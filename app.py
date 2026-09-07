import os
import tempfile
import glob
import uuid
import threading
import json
import time
import re
import shutil
from flask import Flask, render_template, request, send_file, Response, jsonify, after_this_request
from core.settings import SettingsManager
from core.downloader import YtDlpDownloader
from core.processor import MusicMetadataProcessor
from typing import Dict, Any

app = Flask(__name__)

# In-memory storage for download jobs
jobs: Dict[str, Dict[str, Any]] = {}
jobs_lock = threading.Lock()

metadata_processor = MusicMetadataProcessor()

def cleanup_old_jobs():
    """Periodically clean up jobs and temporary folders older than 15 minutes."""
    while True:
        time.sleep(300)
        now = time.time()
        with jobs_lock:
            to_delete = [
                job_id for job_id, job in jobs.items()
                if now - job.get('created_at', now) > 900
            ]
            for job_id in to_delete:
                job = jobs.pop(job_id, None)
                if job and job.get('temp_dir') and os.path.exists(job['temp_dir']):
                    try:
                        shutil.rmtree(job['temp_dir'], ignore_errors=True)
                    except Exception:
                        pass

cleanup_thread = threading.Thread(target=cleanup_old_jobs, daemon=True)
cleanup_thread.start()

class JobManager:
    @staticmethod
    def update_progress(job_id: str, d: Dict[str, Any]):
        with jobs_lock:
            if job_id in jobs:
                if d.get('status') == 'downloading':
                    downloaded = d.get('downloaded_bytes')
                    total = d.get('total_bytes') or d.get('total_bytes_estimate')
                    if downloaded and total and total > 0:
                        jobs[job_id]['progress'] = round((downloaded / total) * 100, 1)
                    else:
                        raw_p = d.get('_percent_str', '0%')
                        clean_p = re.sub(r'\x1b\[[0-9;]*m', '', raw_p).replace('%', '').strip()
                        try:
                            jobs[job_id]['progress'] = float(clean_p)
                        except ValueError:
                            pass
                    jobs[job_id]['status'] = 'İndiriliyor...'
                elif d.get('status') == 'finished':
                    jobs[job_id]['progress'] = 100
                    jobs[job_id]['status'] = 'Dönüştürülüyor...'

def run_download(job_id: str, url: str, temp_dir: str):
    try:
        request_settings = SettingsManager()
        request_settings.set("output_folder", temp_dir)
        request_settings.set("ffmpeg_location", None)

        downloader = YtDlpDownloader(processor=metadata_processor)

        def hook(d):
            JobManager.update_progress(job_id, d)

        downloader.download(url, request_settings, progress_hook=hook)

        # Find the result file (.mp3)
        downloaded_files = [
            os.path.join(temp_dir, f) for f in os.listdir(temp_dir)
            if f.endswith('.mp3')
        ] if os.path.exists(temp_dir) else []

        if downloaded_files:
            file_path = downloaded_files[0]
            filename = os.path.basename(file_path)
            with jobs_lock:
                jobs[job_id]['file_path'] = file_path
                jobs[job_id]['filename'] = filename
                jobs[job_id]['status'] = 'Tamamlandı'
                jobs[job_id]['completed'] = True
                jobs[job_id]['progress'] = 100
        else:
            with jobs_lock:
                jobs[job_id]['status'] = 'Ses dosyası oluşturulamadı.'
                jobs[job_id]['error'] = True

    except Exception as e:
        err_msg = str(e)
        if "FFmpeg bulunamadı" in err_msg:
            clean_err = err_msg
        elif "No video formats found" in err_msg or "Requested format is not available" in err_msg:
            clean_err = "Bu video için uygun ses formatı bulunamadı."
        elif "Private video" in err_msg or "Sign in" in err_msg:
            clean_err = "Bu video gizli veya erişim izni gerektiriyor."
        elif "Video unavailable" in err_msg:
            clean_err = "Video mevcut değil veya kaldırılmış."
        else:
            clean_err = f"İndirme hatası: {err_msg}"

        with jobs_lock:
            jobs[job_id]['status'] = clean_err
            jobs[job_id]['error'] = True

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def start_download():
    url = request.form.get('url')
    if not url:
        return jsonify({"error": "Lütfen bir URL girin"}), 400

    job_id = str(uuid.uuid4())
    temp_dir = tempfile.mkdtemp(prefix="mpthree_")

    with jobs_lock:
        jobs[job_id] = {
            "status": "Başlatılıyor...",
            "progress": 0,
            "completed": False,
            "error": False,
            "file_path": None,
            "temp_dir": temp_dir,
            "created_at": time.time()
        }

    # Start download in a background thread
    thread = threading.Thread(target=run_download, args=(job_id, url, temp_dir))
    thread.start()

    return jsonify({"job_id": job_id})

@app.route('/progress/<job_id>')
def progress(job_id):
    def generate():
        while True:
            with jobs_lock:
                if job_id not in jobs:
                    break
                job = jobs[job_id]
                data = json.dumps({
                    "status": job['status'],
                    "progress": job['progress'],
                    "completed": job['completed'],
                    "error": job['error'],
                    "filename": job.get('filename', '')
                })
                yield f"data: {data}\n\n"
                if job['completed'] or job['error']:
                    break
            time.sleep(0.5)

    return Response(generate(), mimetype='text/event-stream')

@app.route('/get-file/<job_id>')
def get_file(job_id):
    with jobs_lock:
        if job_id not in jobs or not jobs[job_id]['completed']:
            return "Dosya hazır değil", 404
        file_path = jobs[job_id]['file_path']
        filename = os.path.basename(file_path)
        temp_dir = jobs[job_id]['temp_dir']

    @after_this_request
    def remove_temp_files(response):
        def delayed_cleanup():
            time.sleep(10)  # Wait for file streaming to finish
            with jobs_lock:
                jobs.pop(job_id, None)
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except Exception:
                    pass

        threading.Thread(target=delayed_cleanup, daemon=True).start()
        return response

    return send_file(file_path, as_attachment=True, download_name=filename)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1966, debug=False)

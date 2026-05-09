import os
import tempfile
import glob
import uuid
import threading
import json
import time
from flask import Flask, render_template, request, send_file, Response, jsonify
from core.settings import SettingsManager
from core.downloader import YtDlpDownloader
from core.processor import MusicMetadataProcessor
from typing import Dict, Any

app = Flask(__name__)

# In-memory storage for download jobs
# In a production app, this would be Redis/Celery
jobs: Dict[str, Dict[str, Any]] = {}
jobs_lock = threading.Lock()

metadata_processor = MusicMetadataProcessor()

class JobManager:
    @staticmethod
    def update_progress(job_id: str, d: Dict[str, Any]):
        with jobs_lock:
            if job_id in jobs:
                if d['status'] == 'downloading':
                    p = d.get('_percent_str', '0%').replace('%', '').strip()
                    try:
                        jobs[job_id]['progress'] = float(p)
                    except ValueError:
                        pass
                    jobs[job_id]['status'] = 'İndiriliyor...'
                elif d['status'] == 'finished':
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

        # Find the result file
        downloaded_files = glob.glob(os.path.join(temp_dir, "*.mp3"))
        if downloaded_files:
            with jobs_lock:
                jobs[job_id]['file_path'] = downloaded_files[0]
                jobs[job_id]['status'] = 'Tamamlandı'
                jobs[job_id]['completed'] = True
        else:
            with jobs_lock:
                jobs[job_id]['status'] = 'Hata: Dosya bulunamadı'
                jobs[job_id]['error'] = True

    except Exception as e:
        with jobs_lock:
            jobs[job_id]['status'] = f"Hata: {str(e)}"
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
            "temp_dir": temp_dir
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
                    "error": job['error']
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
    
    return send_file(file_path, as_attachment=True, download_name=filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=1966, debug=False)

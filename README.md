# mpThree 🎵

YouTube videolarını yüksek kalitede MP3'e dönüştüren, Dockerize edilmiş web uygulaması.

## ✨ Özellikler

- **⚡ Hızlı İndirme** — `yt-dlp` ile eş zamanlı parça indirme
- **📊 Canlı İlerleme** — SSE (Server-Sent Events) ile anlık ilerleme çubuğu
- **🏷️ Metadata Temizleme** — Otomatik başlık/sanatçı düzenleme, thumbnail gömme
- **🐳 Docker Ready** — Tek komutla çalıştır
- **🧹 Otomatik Temizlik** — İndirme sonrası geçici dosyalar silinir

## 🛠️ Tech Stack

| Katman | Teknoloji |
|---|---|
| Backend | Python 3.12, Flask, Gunicorn (gevent worker) |
| İndirme | yt-dlp, FFmpeg |
| Frontend | Vanilla JS, CSS3 |
| Deploy | Docker |

## 🚀 Hızlı Başlangıç (Docker)

[Docker](https://www.docker.com/) kurulu olduğundan emin olun.

```bash
# Repoyu klonla
git clone https://github.com/ikriyusuf/mpThree.git
cd mpThree

# Tek container olarak çalıştır
docker compose up --build
```

Ardından tarayıcıda [http://localhost:1966](http://localhost:1966) adresini aç.

## 💻 Yerel Geliştirme

FFmpeg sisteminizde PATH'e eklenmiş olmalı.

```bash
pip install -r requirements.txt
python app.py
```

## ⚙️ Yapılandırma

`core/settings.py` üzerinden:
- Ses kalitesi (varsayılan: 192 kbps)
- Ses formatı (varsayılan: mp3)

---
*Made with ❤️*

# mpThree 🎵

YouTube videolarını yüksek kaliteli MP3 ses dosyalarına dönüştüren, sade, şık ve modern arayüze sahip Dockerize edilmiş web uygulaması.

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12%20%7C%203.14-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.x-black?logo=flask&logoColor=white)
![yt-dlp](https://img.shields.io/badge/yt--dlp-latest-red)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green)

</div>

---

## ✨ Özellikler

- **⚡ Hızlı ve Güvenilir İndirme** — Güncel `yt-dlp` motoru ile yüksek kaliteli ses çekme.
- **🎨 Sade ve Şık Arayüz** — Modern karanlık tema (dark mode), cam efekti (glassmorphism), akıcı geçişler ve panodan tek tıkla yapıştırma desteği.
- **📊 Canlı İlerleme Takibi** — SSE (Server-Sent Events) ile anlık indirme yüzdesi ve aşama bildirimi.
- **🏷️ Otomatik Metadata & Kapak Resmi** — Şarkı ve sanatçı adını temizleme, ID3 etiketleme ve kapak resmini (thumbnail) doğrudan MP3 içine gömme.
- **🐳 Docker Ready** — Tek komutla sıfır kurulum zahmetiyle ayağa kaldırılabilir.
- **💻 Yerel Geliştirme ve Taşınabilir FFmpeg** — FFmpeg'i sistem PATH'ine eklemeden doğrudan proje içine `ffmpeg/` veya `bin/` klasörü olarak koyup anında çalıştırma desteği.
- **🧹 Otomatik Temizlik** — İndirilen ve dönüştürülen geçici dosyalar kullanıcıya iletildikten sonra güvenle temizlenir.

---

## 🛠️ Teknoloji Yığını

| Alan | Teknolojiler |
|---|---|
| **Backend** | Python 3.12 / 3.14, Flask, Gunicorn (`gevent` worker) |
| **İndirme Motoru** | `yt-dlp` (Saf Python) |
| **Ses & Metadata** | FFmpeg, Mutagen |
| **Frontend** | Vanilla JS, Modern CSS3 (Glassmorphism, CSS Variables, Responsive) |
| **Dağıtım** | Docker, Docker Compose |

---

## 🚀 Hızlı Başlangıç (Docker ile)

Sisteminizde [Docker](https://www.docker.com/) kuruluysa:

```bash
# 1. Repoyu klonlayın
git clone https://github.com/ikriyusuf/mpThree.git
cd mpThree

# 2. Container'ı derleyin ve başlatın
docker compose up --build
```

Tarayıcınızdan **[http://localhost:1966](http://localhost:1966)** adresine giderek hemen kullanmaya başlayabilirsiniz!

---

## 💻 Yerel Geliştirme (Local)

Docker olmadan yerel makinenizde çalıştırmak için:

```bash
# 1. Bağımlılıkları yükleyin (yalnızca saf Python paketleri)
pip install -r requirements.txt

# 2. FFmpeg Kurulumu / Yerel Klasör:
# - FFmpeg sisteminizde (PATH) kurulu ise otomatik algılanır.
# - Kurulu değilse FFmpeg'i indirip proje içerisindeki 'ffmpeg' veya 'bin' klasörüne koyabilirsiniz:
#   Örn: mpThree/ffmpeg/ffmpeg.exe veya mpThree/bin/ffmpeg.exe

# 3. Uygulamayı başlatın
python app.py
```

---

## 📁 Proje Yapısı

```text
mpThree/
├── app.py                  # Flask web sunucusu, SSE ve indirme iş yöneticisi
├── core/
│   ├── downloader.py       # yt-dlp entegrasyonu, EJS ve FFmpeg çözümleme
│   ├── processor.py        # Metadata temizleme ve ID3 dosya isimlendirme
│   ├── settings.py         # Uygulama ayarları
│   └── interfaces.py       # Arayüz ve sözleşme tanımları
├── templates/
│   └── index.html          # Sade ve şık tek sayfa modern kullanıcı arayüzü
├── Dockerfile              # Python, FFmpeg ve Node.js içeren üretim imajı
├── docker-compose.yml      # Kolay container orchestration
└── requirements.txt        # Python paket bağımlılıkları
```

---

## ⚙️ Yapılandırma

`core/settings.py` dosyası üzerinden varsayılan parametreleri düzenleyebilirsiniz:
- **Ses Kalitesi:** Varsayılan `192` kbps (dilerseniz `320` kbps yapabilirsiniz)
- **Ses Formatı:** Varsayılan `mp3`

---

## 📄 Lisans

Bu proje MIT lisansı ile lisanslanmıştır.

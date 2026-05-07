# CLAUDE.md — Nexora Electronics WhatsApp RAG Bot

## Ringkasan Proyek
WhatsApp customer service bot berbasis RAG (Retrieval-Augmented Generation) untuk toko aksesoris komputer dan gadget fiktif bernama **Nexora Electronics**. Dibuat sebagai proyek portofolio Upwork.

Bot menerima pesan WhatsApp via Twilio, mencari informasi relevan dari ChromaDB (vector store), lalu menghasilkan jawaban dengan GPT-4o-mini yang sadar konteks percakapan sebelumnya.

---

## Tech Stack
- **LLM:** OpenAI GPT-4o-mini
- **Embedding:** OpenAI text-embedding-3-small
- **RAG Framework:** LangChain (langchain, langchain-openai, langchain-chroma, langchain-text-splitters)
- **Vector Database:** ChromaDB (persist ke folder `chroma_db/`, di-generate saat startup)
- **Conversation History:** SQLite (`nexora.db`, di-generate saat startup)
- **Messaging:** Twilio WhatsApp API
- **Web Framework:** FastAPI + Uvicorn
- **Package Manager:** uv
- **Deployment:** Railway (auto-deploy dari GitHub)
- **Python:** 3.12

---

## Struktur File

```
├── app/
│   └── services/
│       ├── admin.py       # FastAPI router /admin — dashboard HTML, HTTP Basic Auth
│       ├── chat.py        # generate_response() — inti: RAG + history + OpenAI + handoff
│       ├── database.py    # SQLite: init_db(), get/save/delete history, get_all_users(), get_stats()
│       ├── rag.py         # ChromaDB: load dokumen, embed, retrieve()
│       └── webhook.py     # FastAPI app, endpoint POST /webhook, lifespan startup
├── data/
│   ├── produk.csv         # 40 produk, 10 kategori, harga USD
│   ├── faq.md             # 28 Q&A pelanggan
│   ├── kebijakan_toko.md  # Kebijakan pengiriman, retur, garansi
│   └── info_toko.md       # Profil toko, jam, kontak, pembayaran
├── main.py                # Entry point: uvicorn dengan PORT dari env
├── Procfile               # Railway start command
├── pyproject.toml         # Dependencies (dikelola uv)
├── GUIDE.md               # Panduan tweaking untuk kebutuhan bisnis
└── .env                   # Secrets (tidak di-commit)
```

---

## Alur Kerja Bot

```
Pesan WhatsApp masuk
  → Twilio POST ke /webhook (Body, From)
  → [handoff check] jika pesan mengandung keyword (mis. "bicara dengan cs"):
      → _notify_admin() — kirim notifikasi WA ke ADMIN_WHATSAPP_NUMBER via Twilio
      → simpan pesan + HANDOFF_REPLY ke SQLite, return langsung (tidak ke OpenAI)
  → retrieve(query) — ambil 5 chunk relevan dari ChromaDB
  → get_history(phone_number) — ambil 10 pesan terakhir dari SQLite
  → OpenAI chat.completions (system prompt + context + history + pesan user)
  → save_message() — simpan pesan user & jawaban bot ke SQLite
  → Twilio MessagingResponse — kirim jawaban balik ke WhatsApp
```

---

## Environment Variables

```env
OPENAI_API_KEY=sk-proj-...
TWILIO_ACCOUNT_SID=ACxxxx...
TWILIO_AUTH_TOKEN=xxxx...
PORT=8000                        # diset otomatis oleh Railway
ADMIN_PASSWORD=admin123          # password HTTP Basic Auth untuk /admin
ADMIN_WHATSAPP_NUMBER=+628xxx    # nomor WA admin penerima notifikasi handoff
TWILIO_WHATSAPP_FROM=+14155238886  # nomor sandbox Twilio (default, bisa dihilangkan)
```

`load_dotenv()` dipanggil di `app/services/chat.py` saat module pertama kali diimport.

---

## Perilaku Startup (Lifespan)

Saat server pertama kali start (`webhook.py` lifespan):
1. `init_db()` — buat tabel `conversations` di SQLite jika belum ada
2. `get_vectorstore()` — cek apakah `chroma_db/chroma.sqlite3` sudah ada:
   - **Ada** → load dari disk (cepat)
   - **Belum ada** → load semua file dari `data/`, split, embed via OpenAI, simpan ke ChromaDB (butuh ~10–30 detik dan beberapa API call)

---

## Command Penting

```bash
# Install dependencies
uv sync

# Jalankan server lokal
uv run python main.py

# Test pipeline tanpa WhatsApp
uv run python -c "
from dotenv import load_dotenv; load_dotenv()
from app.services.database import init_db
from app.services.rag import get_vectorstore
from app.services.chat import generate_response
init_db(); get_vectorstore()
print(generate_response('+628xxx', 'Ada keyboard mechanical tidak?'))
"

# Reset vector store (wajib setelah ubah data/)
rm -rf chroma_db/

# Expose lokal ke internet (untuk testing dengan Twilio)
ngrok http 8000
```

---

## Admin Dashboard

- URL: `http://localhost:8000/admin/` (lokal) atau `https://nama-app.up.railway.app/admin/`
- Auth: HTTP Basic — username bebas, password dari env var `ADMIN_PASSWORD` (default: `admin123`)
- Fitur:
  - 3 stat cards: total pengguna, total pesan, pesan hari ini (`get_stats()`)
  - Bar chart aktivitas pesan 14 hari terakhir (Chart.js via CDN, tidak perlu install)
  - Tabel semua user dengan tombol Lihat History & Hapus
  - Halaman history per user dengan chat bubble + timestamp
- Implementasi: pure FastAPI + inline HTML/CSS, tanpa Streamlit atau framework frontend
- Chart.js dimuat dari CDN `cdn.jsdelivr.net` — butuh koneksi internet saat buka dashboard

## Handoff ke Human Agent

- Trigger: pesan mengandung keyword seperti "bicara dengan cs", "hubungi admin", "talk to human", dll.
- Keyword list ada di `HANDOFF_KEYWORDS` di `app/services/chat.py`
- Notifikasi dikirim via Twilio ke `ADMIN_WHATSAPP_NUMBER` menggunakan `TwilioClient`
- Nomor admin **harus sudah join Twilio sandbox** untuk bisa menerima notifikasi
- Twilio sandbox session expire setelah 24 jam tidak aktif — user dan admin perlu re-join jika sudah lama

---

## Hal Penting saat Modifikasi

- **Setiap perubahan di `data/`** → wajib `rm -rf chroma_db/` dan restart server agar vector store dibangun ulang dengan data terbaru
- **File `.md` baru di `data/`** → otomatis terbaca oleh `rag.py` (pakai `glob("*.md")`), tidak perlu ubah kode
- **File CSV tambahan** → perlu tambahkan loader manual di `rag.py`
- **Ganti model embedding** → wajib reset vector store karena dimensi vektor berbeda
- **`chroma_db/` dan `nexora.db`** → ada di `.gitignore`, tidak di-push ke GitHub, di-generate ulang di Railway setiap deploy
- **System prompt bot** → ada di variabel `SYSTEM_PROMPT` di `app/services/chat.py`
- **Panduan lengkap tweaking** → lihat `GUIDE.md`

---

## Deployment (Railway)

- Start command diambil dari `Procfile`: `uv run uvicorn app.services.webhook:app --host 0.0.0.0 --port $PORT`
- Auto-deploy setiap push ke branch `main` di GitHub
- Environment variables diset di Railway dashboard (bukan dari `.env`)
- Twilio webhook URL: `https://nama-app.up.railway.app/webhook`

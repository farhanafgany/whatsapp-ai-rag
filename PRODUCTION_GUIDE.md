# Panduan Production — Dari Portfolio ke Proyek Real

Panduan ini menjelaskan semua yang perlu kamu ketahui saat mengerjakan proyek WhatsApp bot sungguhan untuk klien, bukan lagi sekedar demo portfolio.

---

## Daftar Isi
1. [Perbedaan Sandbox vs Production](#1-perbedaan-sandbox-vs-production)
2. [Memahami Ekosistem WhatsApp Business API](#2-memahami-ekosistem-whatsapp-business-api)
3. [Langkah Setup Production via Twilio](#3-langkah-setup-production-via-twilio)
4. [Konsep Penting: Session vs Template Message](#4-konsep-penting-session-vs-template-message)
5. [Struktur Biaya yang Harus Dijelaskan ke Klien](#5-struktur-biaya-yang-harus-dijelaskan-ke-klien)
6. [Upgrade Infrastruktur untuk Production](#6-upgrade-infrastruktur-untuk-production)
7. [Keamanan yang Wajib Ditambahkan](#7-keamanan-yang-wajib-ditambahkan)
8. [Hal-hal yang Sering Bikin Kaget di Lapangan](#8-hal-hal-yang-sering-bikin-kaget-di-lapangan)

---

## 1. Perbedaan Sandbox vs Production

| Aspek | Sandbox (Portofolio) | Production (Real) |
|---|---|---|
| Siapa yang bisa dikirimi | Hanya nomor yang sudah join sandbox | Semua nomor WhatsApp di dunia |
| Proses setup | Langsung pakai, 5 menit | Perlu approval Meta (2–7 hari kerja) |
| Biaya | Gratis | Berbayar (per pesan + conversation fee) |
| Nomor pengirim | Nomor milik Twilio (+1415xxx) | Nomor dedicated milik bisnis klien |
| Nama pengirim di WhatsApp | "Twilio Sandbox" | Nama bisnis klien (misal: "Nexora Electronics") |
| Batas pesan | Ada | Bertahap naik sesuai tier bisnis |
| Template message | Tidak perlu | Wajib untuk pesan yang dimulai bisnis |

---

## 2. Memahami Ekosistem WhatsApp Business API

Ini hal yang paling penting untuk dipahami. Ada **3 pihak** yang terlibat:

```
Meta (WhatsApp)
    ↓ memberikan akses API
Twilio (BSP / Business Solution Provider)
    ↓ menyediakan wrapper API yang lebih mudah dipakai
Kamu / Klien (developer & pemilik bisnis)
```

**Meta** adalah pemilik WhatsApp. Mereka yang menentukan aturan, approval, dan pricing dasar.

**Twilio** adalah salah satu BSP (Business Solution Provider) resmi Meta. Mereka menyederhanakan akses ke WhatsApp Business API. Alternatif BSP selain Twilio: Vonage, MessageBird, WATI, Respond.io.

**Implikasi:** Kamu tidak bisa langsung pakai WhatsApp API tanpa melalui BSP yang disetujui Meta.

### Apa yang Dibutuhkan Klien untuk Production

- **Meta Business Account** (bisa buat di business.facebook.com)
- **Verifikasi bisnis Meta** — Meta akan minta dokumen legalitas bisnis
- **Nomor telepon dedicated** — nomor ini khusus untuk WhatsApp bisnis, tidak bisa dipakai WhatsApp personal lagi setelah didaftarkan
- **Akun Twilio** (atau BSP lain) yang sudah terhubung ke Meta Business

---

## 3. Langkah Setup Production via Twilio

### Tahap 1 — Persiapan di sisi klien
1. Buat **Meta Business Account** di [business.facebook.com](https://business.facebook.com)
2. Lengkapi **Business Verification** Meta:
   - Upload dokumen legalitas bisnis (akta perusahaan, SIUP, atau yang setara)
   - Proses verifikasi: 1–5 hari kerja
   - Tanpa verifikasi, akun dibatasi hanya bisa kirim 250 percakapan/hari
3. Siapkan **nomor telepon dedicated** untuk bisnis — bisa nomor baru atau nomor yang sudah ada, asal belum dipakai di WhatsApp manapun

### Tahap 2 — Setup di Twilio Console
1. Login Twilio → **Messaging** → **Senders** → **WhatsApp Senders**
2. Klik **"Request Access"** → ikuti proses menghubungkan Twilio ke Meta Business Account klien
3. Daftarkan nomor dedicated klien sebagai WhatsApp Business number
4. Pilih **Display Name** (nama bisnis yang muncul di WhatsApp penerima) → submit untuk approval Meta
5. Tunggu approval: biasanya 1–3 hari kerja

### Tahap 3 — Konfigurasi Webhook
Sama seperti sandbox, tapi kali ini menggunakan nomor production:
1. Di Twilio Console → WhatsApp Sender yang sudah approved
2. Set webhook URL ke URL production klien: `https://domain-klien.com/webhook`
3. Method: POST

### Tahap 4 — Update kode (minimal)
Tidak banyak yang perlu diubah di kode. Yang berubah hanyalah:
- Nomor pengirim Twilio (`From` number) — ini dihandle Twilio secara otomatis
- Pastikan `TWILIO_ACCOUNT_SID` dan `TWILIO_AUTH_TOKEN` di `.env` adalah milik akun production

---

## 4. Konsep Penting: Session vs Template Message

Ini adalah konsep yang **wajib kamu pahami** sebelum meeting dengan klien.

### Session Message (Pesan dalam Sesi)
- Dipicu oleh **pelanggan yang kirim pesan lebih dulu**
- Setelah pelanggan kirim pesan pertama, bisnis punya **jendela 24 jam** untuk membalas dengan pesan apapun (bebas format)
- Bot customer service seperti yang kita buat bekerja dalam mode ini
- **Biaya lebih murah** (user-initiated conversation)

### Template Message (Pesan di Luar Sesi)
- Dipakai ketika bisnis ingin **menghubungi pelanggan lebih dulu** atau setelah jendela 24 jam tutup
- Template **harus disetujui Meta terlebih dahulu** sebelum bisa dipakai (proses approval: 1–2 hari)
- Format kaku: teks dengan variabel (tidak bisa bebas)
- Contoh use case: konfirmasi order, notifikasi pengiriman, reminder pembayaran
- **Biaya lebih mahal** (business-initiated conversation)

**Contoh template yang perlu diajukan ke Meta:**
```
Halo {{1}}, pesanan kamu #{{2}} sedang dalam perjalanan dan 
estimasi tiba {{3}}. Terima kasih telah berbelanja di Nexora Electronics!
```

### Implikasi untuk Bot Customer Service
Bot kita (yang sudah dibuat) hanya butuh **session message** karena selalu menunggu pelanggan kirim pesan lebih dulu. Template message baru dibutuhkan jika klien ingin fitur proaktif seperti notifikasi atau broadcast.

---

## 5. Struktur Biaya yang Harus Dijelaskan ke Klien

Ini sering jadi sumber kebingungan. Ada **dua lapis biaya**:

### Biaya Twilio (per pesan)
- Inbound message (pesan masuk dari pelanggan): ~$0.005/pesan
- Outbound message (balasan bot): ~$0.005/pesan
- Cek harga terbaru di: twilio.com/whatsapp/pricing

### Biaya WhatsApp/Meta (per conversation)
Meta menghitung biaya per **conversation** (bukan per pesan), berlaku 24 jam:

| Tipe Conversation | Estimasi Biaya |
|---|---|
| User-initiated (pelanggan mulai duluan) | ~$0.01–$0.05 per conversation |
| Business-initiated (bisnis mulai duluan) | ~$0.05–$0.15 per conversation |
| Service conversation (customer service) | Gratis di beberapa negara |

> Harga bervariasi per negara. Cek harga spesifik di: developers.facebook.com/docs/whatsapp/pricing

### 1000 Conversation Gratis per Bulan
Meta memberikan **1000 conversation gratis per bulan** untuk setiap bisnis. Cukup untuk bisnis kecil yang baru mulai.

### Cara Jelaskan ke Klien
Sampaikan ke klien bahwa ada biaya operasional bulanan yang terdiri dari:
1. Biaya Twilio (tagihan ke akun Twilio klien)
2. Biaya Meta/WhatsApp (sudah termasuk dalam tagihan Twilio, atau terpisah tergantung setup)
3. Biaya Railway/hosting untuk bot
4. Biaya OpenAI API (per token yang digunakan)

Untuk bisnis kecil-menengah dengan ~500 conversation/bulan, total biaya operasional biasanya di bawah $20/bulan.

---

## 6. Upgrade Infrastruktur untuk Production

Beberapa komponen yang ada di proyek portofolio ini perlu diupgrade untuk production sungguhan:

### SQLite → PostgreSQL
SQLite tidak cocok untuk production karena:
- Tidak mendukung concurrent write dengan baik
- File-based, tidak cocok untuk multi-instance deployment
- Railway menyediakan PostgreSQL add-on yang mudah di-setup

**Cara upgrade:**
1. Tambahkan Railway PostgreSQL add-on
2. Ganti library `sqlite3` dengan `psycopg2` atau `asyncpg`
3. Update connection string dari file path ke DATABASE_URL

### ChromaDB Persistent Storage
Di deployment sekarang, ChromaDB di-rebuild setiap deploy (karena Railway filesystem ephemeral). Untuk production:
- Pakai **Railway Volume** (persistent disk) untuk menyimpan `chroma_db/`
- Atau migrasi ke vector database cloud seperti **Pinecone** atau **Supabase pgvector**
- Ini penting jika dataset besar dan proses embedding memakan waktu lama

### Railway Plan
- Free tier ($5/bulan) cukup untuk portofolio
- Untuk production dengan traffic nyata, upgrade ke **Hobby plan ($5/bulan fixed)** atau **Pro plan**

### Variabel Environment yang Perlu Ditambah
```env
# Production
DATABASE_URL=postgresql://...     # jika upgrade ke PostgreSQL
TWILIO_AUTH_TOKEN=...             # untuk validasi signature webhook
```

---

## 7. Keamanan yang Wajib Ditambahkan

Proyek portofolio ini tidak punya validasi keamanan — tidak apa-apa untuk demo, tapi **wajib ditambahkan di production**.

### Validasi Signature Twilio
Tanpa ini, siapapun bisa kirim request palsu ke endpoint `/webhook` kamu.

Tambahkan di `app/services/webhook.py`:

```python
from twilio.request_validator import RequestValidator
from fastapi import Request, HTTPException
import os

validator = RequestValidator(os.getenv("TWILIO_AUTH_TOKEN"))

@app.post("/webhook")
async def webhook(request: Request, Body: str = Form(), From: str = Form()):
    # Validasi bahwa request benar-benar dari Twilio
    signature = request.headers.get("X-Twilio-Signature", "")
    url = str(request.url)
    form_data = dict(await request.form())
    
    if not validator.validate(url, form_data, signature):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")
    
    reply = generate_response(phone_number=From, user_message=Body)
    response = MessagingResponse()
    response.message(reply)
    return Response(content=str(response), media_type="application/xml")
```

### Pembatasan Panjang Pesan
Cegah input yang terlalu panjang sebelum dikirim ke OpenAI:
```python
# Di app/services/chat.py
def generate_response(phone_number: str, user_message: str) -> str:
    user_message = user_message[:1000]  # batasi 1000 karakter
    ...
```

### Rate Limiting
Cegah satu nomor spam bot dengan ratusan pesan:
```python
# Tambahkan library: slowapi
from slowapi import Limiter
from slowapi.util import get_remote_address
```

---

## 8. Hal-hal yang Sering Bikin Kaget di Lapangan

### "Kenapa approval Meta lama sekali?"
Meta kadang butuh 5–7 hari bahkan lebih. Ini normal dan tidak bisa dipercepat. Informasikan ke klien sejak awal agar tidak panik.

### "Nomor sudah dipakai WhatsApp personal, bisa dipindah?"
Bisa, tapi nomornya tidak bisa dipakai WhatsApp personal lagi selamanya setelah dimigrasi ke Business API. Sarankan klien pakai nomor baru.

### "Pelanggan bisa reply kapan saja, bot harus selalu aktif"
Ya. Berbeda dengan sandbox yang bisa mati saat testing, production bot harus **24/7 uptime**. Pastikan Railway (atau hosting apapun) tidak punya downtime tanpa monitoring.

### "Display name ditolak Meta"
Meta cukup ketat soal display name. Harus sesuai nama bisnis yang terverifikasi. Nama generik seperti "Customer Service" atau "CS Bot" sering ditolak.

### "Template message tidak disetujui"
Meta menolak template yang terlalu promosi atau tidak jelas use case-nya. Tulis template yang benar-benar utilitarian (konfirmasi, notifikasi) bukan iklan.

### "Klien mau blast promosi ke semua pelanggan"
Ini butuh **template message yang diapprove** dan database nomor pelanggan yang sudah **opt-in** (setuju menerima pesan). Jika tidak, akun WhatsApp Business klien bisa kena ban. Jelaskan ini ke klien sebelum mulai.

### "OpenAI API tiba-tiba lambat atau error"
Selalu tangani error dari OpenAI API secara graceful — jangan biarkan bot diam tanpa balasan. Tambahkan fallback message seperti:
```python
try:
    answer = response.choices[0].message.content
except Exception:
    answer = "Maaf, saya sedang mengalami gangguan teknis. Silakan coba beberapa saat lagi atau hubungi support@nexoraelectronics.com"
```

### "Klien mau bot bisa kirim gambar/dokumen"
WhatsApp Business API mendukung media (gambar, PDF, video). Ini fitur tambahan yang perlu dikoding terpisah menggunakan Twilio Media API — bukan bagian dari setup dasar.

---

## 9. Skill yang Harus Dikuasai Sebelum Proyek Real Datang

Jangan tunggu dapat proyek dulu baru belajar hal-hal ini. Kuasai lebih awal agar tidak kewalahan saat ada klien yang menunggu.

### Kuasai berbagai format data klien

Di dunia nyata, klien jarang punya data serapi CSV. Mereka datang dengan berbagai format:

| Format | Library yang dipakai |
|---|---|
| PDF katalog / dokumen | `pypdf` atau `langchain_community.document_loaders.PyPDFLoader` |
| Google Sheets | `gspread` + konversi ke CSV |
| Website / halaman produk | `langchain_community.document_loaders.WebBaseLoader` |
| Word (.docx) | `python-docx` atau `langchain_community.document_loaders.Docx2txtLoader` |
| Tabel di Excel | `pandas` + konversi ke teks |

Latihan: coba load masing-masing format ini ke pipeline RAG yang sudah ada, lalu lihat hasilnya di ChromaDB.

### Prompt engineering untuk berbagai konteks bisnis

System prompt menentukan kepribadian dan batasan bot. Setiap klien butuh prompt yang berbeda. Yang perlu dilatih:
- Cara membatasi topik (bot hanya jawab soal produk, tolak pertanyaan di luar itu)
- Cara mengatur tone (formal untuk bank/asuransi, santai untuk toko retail)
- Cara instruksikan bot untuk selalu minta klarifikasi jika pertanyaan ambigu
- Cara paksa bot jawab dalam format tertentu (misalnya selalu sertakan harga dan stok)

Latihan: ambil 3 jenis bisnis berbeda (restoran, klinik, toko fashion), tulis system prompt yang berbeda untuk masing-masing, lalu test responsnya.

### Mengelola ekspektasi klien non-teknis

Ini skill non-teknis yang sama pentingnya dengan coding. Klien sering berekspektasi:
- Bot bisa jawab **semua** pertanyaan → padahal bot hanya sebaik datanya
- Bot tidak pernah salah → padahal LLM bisa hallucinate
- Bot bisa langsung live dalam sehari → padahal ada approval Meta yang butuh waktu

**Cara jelaskan ke klien:**
> "Bot ini bekerja seperti karyawan baru yang sudah diberi buku panduan lengkap — dia hanya bisa menjawab berdasarkan isi buku itu. Kalau ada pertanyaan yang tidak ada di buku, dia akan jujur bilang tidak tahu dan meneruskan ke tim manusia."

Dengan analogi seperti ini, klien lebih mudah paham keterbatasan AI tanpa merasa ditipu.

### Buat alur update data yang jelas untuk klien

Setelah bot live, klien akan rutin minta update — harga berubah, produk baru, promo berganti. Sejak awal, tentukan salah satu dari dua model:

**Model A — Klien update sendiri:**
- Beri klien akses ke file CSV/MD di Google Drive atau GitHub
- Klien edit file, lalu kamu rebuild vector store dan redeploy
- Cocok untuk klien yang mau terlibat dan update sering

**Model B — Kamu yang handle (maintenance retainer):**
- Klien kirim permintaan update via WhatsApp atau email
- Kamu update file dan redeploy, tagih biaya maintenance bulanan
- Cocok untuk klien non-teknis yang tidak mau repot
- Ini sumber pendapatan recurring yang bagus sebagai freelancer

Tentukan model ini di awal proyek dan masukkan ke kontrak.

### Basic monitoring — tahu sebelum klien laporan

Tahu kapan bot mati atau error sebelum klien yang laporan duluan adalah tanda profesionalisme. Minimal:

- **Railway** → aktifkan email notifikasi jika deployment gagal
- **UptimeRobot** (gratis) → monitor URL `/webhook` dan kirim notifikasi jika down
- **Pantau usage OpenAI** → set spending limit di dashboard OpenAI agar tidak tiba-tiba habis kuota tanpa tahu
- **Log sederhana** → tambahkan `print()` atau Python `logging` di webhook untuk catat setiap pesan masuk dan error

Untuk proyek lebih serius, gunakan **Sentry** (error tracking) yang ada free tier-nya.

---

## Ringkasan Checklist untuk Proyek Real

**Sebelum mulai development:**
- [ ] Pastikan klien punya Meta Business Account
- [ ] Mulai proses Business Verification Meta lebih awal (bisa jalan paralel)
- [ ] Tentukan nomor dedicated untuk WhatsApp bisnis
- [ ] Diskusikan biaya operasional bulanan dengan klien

**Saat development:**
- [ ] Tambahkan validasi Twilio signature
- [ ] Gunakan PostgreSQL, bukan SQLite
- [ ] Setup ChromaDB persistent storage
- [ ] Tambahkan rate limiting dan input sanitization
- [ ] Tambahkan error handling untuk API failure
- [ ] Setup monitoring/alerting (Railway metrics atau Sentry)

**Sebelum go-live:**
- [ ] Test dengan nomor production (bukan sandbox)
- [ ] Pastikan template message sudah diapprove Meta (jika perlu)
- [ ] Briefing klien tentang aturan WhatsApp Business Policy
- [ ] Pastikan ada mekanisme opt-in jika klien ingin kirim pesan proaktif
- [ ] Dokumentasikan cara update dataset dan restart bot ke klien

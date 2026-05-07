# Panduan Tweaking — Nexora Electronics WhatsApp Bot

Panduan ini menjelaskan cara menyesuaikan bot untuk kebutuhan bisnis yang berbeda.

---

## Daftar Isi
1. [Mengganti nama & kepribadian bot](#1-mengganti-nama--kepribadian-bot)
2. [Mengubah dataset produk](#2-mengubah-dataset-produk)
3. [Mengubah FAQ & kebijakan toko](#3-mengubah-faq--kebijakan-toko)
4. [Reset vector store setelah ubah data](#4-reset-vector-store-setelah-ubah-data)
5. [Mengubah model LLM atau embedding](#5-mengubah-model-llm-atau-embedding)
6. [Mengatur jumlah hasil retrieval (RAG)](#6-mengatur-jumlah-hasil-retrieval-rag)
7. [Mengatur panjang history percakapan](#7-mengatur-panjang-history-percakapan)
8. [Menghapus history percakapan user](#8-menghapus-history-percakapan-user)
9. [Menambah kategori data baru](#9-menambah-kategori-data-baru)
10. [Checklist deploy ulang ke Railway](#10-checklist-deploy-ulang-ke-railway)

---

## 1. Mengganti nama & kepribadian bot

**File:** `app/services/chat.py`

Cari variabel `SYSTEM_PROMPT` dan ubah sesuai kebutuhan:

```python
SYSTEM_PROMPT = """\
Kamu adalah Nex, asisten customer service virtual Nexora Electronics...
```

**Contoh perubahan untuk bisnis lain:**
```python
SYSTEM_PROMPT = """\
Kamu adalah Sari, asisten customer service virtual TechMart Indonesia — 
toko laptop dan komputer terkemuka di Jakarta.
...
"""
```

Yang bisa diubah:
- **Nama bot** — ganti `Nex` dengan nama lain
- **Nama toko** — ganti `Nexora Electronics` dengan nama bisnis
- **Fokus layanan** — sesuaikan daftar tugas bot
- **Tone** — tambahkan instruksi seperti "gunakan bahasa santai" atau "gunakan bahasa formal"
- **Email/website** — ganti kontak default jika informasi tidak ditemukan

---

## 2. Mengubah dataset produk

**File:** `data/produk.csv`

Format kolom (jangan ubah nama kolom):
```
id, nama_produk, kategori, brand, model, harga_usd, stok, deskripsi
```

**Menambah produk baru:**
Tambahkan baris baru di akhir file. Pastikan `id` unik (lanjutkan dari nomor terakhir).

```csv
P041,Logitech MX Keys Mini Wireless Keyboard,Keyboard,Logitech,MX Keys Mini,99.99,20,Keyboard wireless compact 65% ...
```

**Mengubah mata uang:**
Ganti nama kolom `harga_usd` menjadi `harga_idr` (misalnya), lalu update `app/services/rag.py` bagian format konten produk:

```python
# Di app/services/rag.py, cari bagian ini:
content = (
    f"Produk: {row['nama_produk']}\n"
    ...
    f"Harga: ${row['harga_usd']}\n"   # <- ubah $ dan nama kolom di sini
    ...
)
```

> **Penting:** Setelah mengubah `produk.csv`, wajib [reset vector store](#4-reset-vector-store-setelah-ubah-data).

---

## 3. Mengubah FAQ & kebijakan toko

**File FAQ:** `data/faq.md`

Format yang digunakan (pertahankan format ini agar chunking optimal):
```markdown
**Q: Pertanyaan di sini?**
A: Jawaban di sini.
```

**File kebijakan:** `data/kebijakan_toko.md`

Edit langsung teks yang ada — misalnya ubah durasi retur dari 14 hari menjadi 30 hari, ubah estimasi pengiriman, dll.

**File info toko:** `data/info_toko.md`

Ganti nama toko, alamat, jam operasional, kontak, dan metode pembayaran.

> **Penting:** Setelah mengubah file `.md` manapun, wajib [reset vector store](#4-reset-vector-store-setelah-ubah-data).

---

## 4. Reset vector store setelah ubah data

Setiap kali ada perubahan di folder `data/`, vector store ChromaDB **harus dihapus** agar dibangun ulang dengan data terbaru.

**Lokal:**
```bash
rm -rf chroma_db/
```
Lalu jalankan ulang server — vector store akan otomatis dibangun ulang saat startup.

**Railway:**
Cukup push perubahan ke GitHub. Karena Railway tidak menyimpan `chroma_db/` antar deploy (filesystem ephemeral), vector store akan otomatis dibangun ulang dari data terbaru setiap kali deploy.

---

## 5. Mengubah model LLM atau embedding

**File:** `app/services/chat.py` dan `app/services/rag.py`

### Ganti model LLM
```python
# app/services/chat.py
response = client.chat.completions.create(
    model="gpt-4o-mini",   # <- ganti di sini
    ...
)
```

Pilihan model OpenAI (dari termurah ke terkuat):
| Model | Kecepatan | Kualitas | Biaya |
|---|---|---|---|
| `gpt-4o-mini` | Cepat | Baik | Murah |
| `gpt-4o` | Sedang | Sangat baik | Sedang |
| `gpt-4-turbo` | Sedang | Sangat baik | Mahal |

### Ganti model embedding

> **Perhatian:** Jika ganti model embedding, wajib reset vector store dan build ulang dari nol karena dimensi vektor berbeda.

```python
# app/services/rag.py
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")  # <- ganti di sini
```

Pilihan:
| Model | Dimensi | Kualitas | Biaya |
|---|---|---|---|
| `text-embedding-3-small` | 1536 | Baik | Murah |
| `text-embedding-3-large` | 3072 | Lebih baik | Lebih mahal |

---

## 6. Mengatur jumlah hasil retrieval (RAG)

**File:** `app/services/rag.py`

Parameter `k` menentukan berapa banyak potongan dokumen yang diambil sebagai konteks:

```python
def retrieve(query: str, k: int = 5) -> str:
```

- **Naikkan `k`** (misalnya `k=8`) → konteks lebih banyak, jawaban lebih lengkap, tapi token lebih boros
- **Turunkan `k`** (misalnya `k=3`) → konteks lebih sedikit, jawaban lebih fokus, token lebih hemat

### Chunk size

Parameter ini menentukan seberapa besar potongan dokumen saat embedding:

```python
# app/services/rag.py
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
```

- **`chunk_size`** — panjang maksimal tiap potongan (dalam karakter). Naikkan jika dokumen punya paragraf panjang yang perlu dibaca utuh.
- **`chunk_overlap`** — tumpang tindih antar potongan agar konteks tidak terputus di tengah kalimat.

> Setelah ubah chunk size, wajib reset vector store.

---

## 7. Mengatur panjang history percakapan

**File:** `app/services/database.py`

Parameter `limit` menentukan berapa banyak pesan terakhir yang disertakan sebagai konteks percakapan:

```python
def get_history(phone_number: str, limit: int = 10) -> list[dict]:
```

`limit=10` artinya 10 pesan terakhir (5 giliran percakapan: 5 user + 5 bot).

- **Naikkan** jika ingin bot ingat konteks lebih panjang (tapi token lebih boros)
- **Turunkan** jika ingin hemat token dan bot cukup ingat 2–3 giliran terakhir

---

## 8. Menghapus history percakapan user

Berguna untuk reset percakapan saat testing, atau jika ingin fitur "reset chat" di masa depan.

Jalankan via Python shell atau tambahkan sebagai endpoint admin:

```python
import sqlite3
conn = sqlite3.connect("nexora.db")

# Hapus semua history semua user
conn.execute("DELETE FROM conversations")

# Hapus history user tertentu
conn.execute("DELETE FROM conversations WHERE phone_number = ?", ("+6281234567890",))

conn.commit()
conn.close()
```

---

## 9. Menambah kategori data baru

Jika bisnis punya data tambahan selain produk (misalnya: daftar cabang toko, promo aktif, jadwal servis), buat file baru di folder `data/`:

**Contoh: `data/promo.md`**
```markdown
# Promo Aktif Nexora Electronics

## Promo Mei 2025
- Diskon 15% untuk semua keyboard mechanical hingga 31 Mei 2025
- Gratis ongkir untuk pembelian headset di atas $50
```

File `.md` baru di folder `data/` akan **otomatis terbaca** oleh `app/services/rag.py` karena menggunakan `DATA_PATH.glob("*.md")`. Tidak perlu ubah kode apapun.

Untuk file CSV tambahan, perlu tambahkan loader-nya di `app/services/rag.py` secara manual.

Setelah tambah file baru, wajib [reset vector store](#4-reset-vector-store-setelah-ubah-data).

---

## 10. Checklist deploy ulang ke Railway

Setiap kali ada perubahan kode atau data:

- [ ] Ubah file yang diperlukan (`data/`, `app/services/`, dll.)
- [ ] Jika data berubah: hapus `chroma_db/` lokal (`rm -rf chroma_db/`)
- [ ] Test lokal: `uv run python main.py`
- [ ] Commit & push ke GitHub:
  ```bash
  git add .
  git commit -m "update: ..."
  git push
  ```
- [ ] Railway akan otomatis redeploy (auto-deploy dari GitHub)
- [ ] Pantau Railway logs untuk pastikan startup berhasil

> `chroma_db/` dan `nexora.db` sudah ada di `.gitignore`, jadi tidak akan ikut ke-push.

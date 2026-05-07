# Alur System — Nexora Electronics WhatsApp Bot

---

## 1. Gambaran Besar Keseluruhan System

```
┌─────────────────────────────────────────────────────────────────────┐
│                        INFRASTRUKTUR                                │
│                                                                     │
│   ┌──────────┐     ┌──────────┐     ┌──────────────────────────┐   │
│   │          │     │          │     │        RAILWAY           │   │
│   │   USER   │────▶│  TWILIO  │────▶│  ┌────────────────────┐  │   │
│   │          │     │(WhatsApp)│     │  │   FastAPI Server   │  │   │
│   │(WhatsApp)│◀────│          │◀────│  └────────────────────┘  │   │
│   └──────────┘     └──────────┘     └──────────────────────────┘   │
│                                                  │                  │
│                              ┌───────────────────┤                  │
│                              │                   │                  │
│                    ┌─────────▼──────┐   ┌────────▼───────┐         │
│                    │   OpenAI API   │   │   ChromaDB     │         │
│                    │  (GPT-4o-mini) │   │ (Vector Store) │         │
│                    └────────────────┘   └────────────────┘         │
│                                                                     │
│                              ┌────────────────────────┐            │
│                              │  SQLite (nexora.db)    │            │
│                              │  (Conversation History)│            │
│                              └────────────────────────┘            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Alur Startup Server (Saat Pertama Kali Jalan)

```
SERVER START (uv run python main.py)
│
├─▶ main.py
│     └─▶ uvicorn.run(app, port=$PORT)
│
└─▶ webhook.py — lifespan()
      │
      ├─▶ [1] database.py — init_db()
      │         │
      │         └─▶ Buat tabel "conversations" di SQLite
      │               jika belum ada
      │               ✓ nexora.db siap
      │
      └─▶ [2] rag.py — get_vectorstore()
                │
                ├─▶ Cek: apakah chroma_db/chroma.sqlite3 ada?
                │
                ├── YA ──▶ Load ChromaDB dari disk
                │              ✓ Vector store siap (cepat)
                │
                └── TIDAK ──▶ _load_documents()
                                  │
                                  ├─▶ Baca data/faq.md
                                  ├─▶ Baca data/info_toko.md
                                  ├─▶ Baca data/kebijakan_toko.md
                                  └─▶ Baca data/produk.csv
                                        (40 produk → format teks)
                                  │
                                  └─▶ RecursiveCharacterTextSplitter
                                            chunk_size=500
                                            chunk_overlap=50
                                        │
                                        └─▶ OpenAI Embeddings API
                                              model: text-embedding-3-small
                                              (ubah teks → vektor angka)
                                            │
                                            └─▶ Simpan ke ChromaDB
                                                  ✓ Vector store siap
                                                  (butuh ~15–30 detik)

      ✓ SERVER SIAP MENERIMA REQUEST
```

---

## 3. Alur Per Pesan (Setiap Kali User Kirim WhatsApp)

```
USER kirim pesan WhatsApp: "Ada mouse gaming tidak?"
│
▼
TWILIO
  Terima pesan dari WhatsApp
  Kirim HTTP POST ke webhook URL:
  POST https://app.railway.app/webhook
  Body: { Body: "Ada mouse gaming tidak?", From: "+6281234567890" }
│
▼
webhook.py — POST /webhook
  Ekstrak: pesan = "Ada mouse gaming tidak?"
           nomor = "+6281234567890"
  Panggil: generate_response(nomor, pesan)
│
▼
chat.py — generate_response()
  │
  ├─▶ [1] rag.py — retrieve(query="Ada mouse gaming tidak?", k=5)
  │         │
  │         └─▶ ChromaDB similarity_search()
  │                 Ubah query → vektor (OpenAI Embeddings)
  │                 Cari 5 chunk paling mirip di vector store
  │                 Return: teks produk mouse yang relevan
  │                 ✓ context = "Produk: Logitech G102...\n
  │                              Produk: Razer DeathAdder..."
  │
  ├─▶ [2] database.py — get_history("+6281234567890", limit=10)
  │         │
  │         └─▶ Query SQLite: 10 pesan terakhir nomor ini
  │                 ✓ history = [ {role: "user", content: "..."},
  │                               {role: "assistant", content: "..."} ]
  │
  ├─▶ [3] Susun messages untuk OpenAI:
  │         [
  │           { role: "system",    content: SYSTEM_PROMPT + context },
  │           { role: "user",      content: "pesan lama..." },      ← history
  │           { role: "assistant", content: "jawaban lama..." },    ← history
  │           { role: "user",      content: "Ada mouse gaming tidak?" }
  │         ]
  │
  ├─▶ [4] OpenAI API — chat.completions.create()
  │         model: gpt-4o-mini
  │         max_tokens: 500
  │         │
  │         └─▶ ✓ answer = "Halo! Kami punya beberapa pilihan
  │                          mouse gaming: Logitech G102 ($24.99)..."
  │
  └─▶ [5] database.py — save_message() × 2
              Simpan pesan user ke SQLite
              Simpan jawaban bot ke SQLite
              ✓ History diperbarui
│
▼
webhook.py
  Buat Twilio MessagingResponse dengan jawaban bot
  Return XML response ke Twilio
│
▼
TWILIO
  Terima XML response
  Kirim pesan balik ke WhatsApp user
│
▼
USER terima jawaban di WhatsApp
```

---

## 4. Peta Tools & Peran Masing-masing

```
┌─────────────────────────────────────────────────────────────────┐
│  LAYER          TOOL                    FUNGSI                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Messaging    [ Twilio ]         Jembatan WhatsApp ↔ server     │
│                                  Terima & kirim pesan WA        │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Web Server   [ FastAPI ]        Terima POST /webhook           │
│               [ Uvicorn ]        Jalankan FastAPI               │
│               [ Railway ]        Hosting server di cloud        │
│               [ ngrok ]          Expose lokal saat development  │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  RAG          [ LangChain ]      Orchestrator pipeline RAG      │
│               [ ChromaDB ]       Simpan & cari vektor dokumen   │
│               [ OpenAI          Ubah teks → angka (vektor)      │
│                 Embeddings ]     model: text-embedding-3-small  │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  LLM          [ OpenAI ]         Generate jawaban natural       │
│               [ GPT-4o-mini ]    model yang digunakan           │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Database     [ SQLite ]         Simpan history percakapan      │
│                                  per nomor WhatsApp             │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Data         [ CSV ]            Katalog 40 produk              │
│               [ Markdown ]       FAQ, kebijakan, info toko      │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Dev Tools    [ uv ]             Package & environment manager  │
│               [ python-dotenv ]  Load .env ke environment       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. Alur Data: Dari File ke Jawaban Bot

```
data/produk.csv          ──┐
data/faq.md              ──┤
data/kebijakan_toko.md   ──┤──▶ LangChain Loader
data/info_toko.md        ──┘         │
                                     ▼
                            RecursiveCharacterTextSplitter
                            (potong jadi chunk 500 karakter)
                                     │
                                     ▼
                            OpenAI text-embedding-3-small
                            (ubah tiap chunk → 1536 angka)
                                     │
                                     ▼
                               ChromaDB (disk)
                            (simpan vektor + teks asli)
                                     │
                         ┌───────────┘
                         │  saat ada pertanyaan masuk:
                         ▼
                    Query user → vektor
                         │
                         ▼
                    Similarity Search
                    (cari 5 chunk paling dekat)
                         │
                         ▼
                    Teks chunk relevan
                    (context untuk GPT-4o-mini)
```
